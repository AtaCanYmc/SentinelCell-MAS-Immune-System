# ADR 011: Final Security & Architecture Maturation

## Status
Accepted

## Context
Projenin üretime (production) hazır olduğu düşünülse de, agresif saldırı senaryoları ve devasa yüksek yük (high-load) koşullarında tespit edilen 5 ekstrem zafiyet bulunmuştur:
1. **LLM DDoS (Wallet Exhaustion):** Sisteme milyonlarca hatalı paket sokularak sınırsız LLM faturası yaratılabilir.
2. **MCP Darboğazı (Single Point of Failure):** FastMCP şema sunucusu kapandığında SentinelCell kilitleniyordu (Fail-Closed).
3. **Gecikme (Latency) Engeli:** LangGraph'ın eşzamanlı çalışması, milisaniye hassasiyetindeki sistemler için kabul edilemez darboğaz oluşturabilir.
4. **DLQ Replay Yokluğu:** Karantinaya alınıp düşürülen mektuplar (.antigravity/logs/dlq.json) kaydediliyor ancak geriye oynatılamıyordu (Replay).
5. **Data Poisoning (Veri Zehirlenmesi):** Prompt Injection uyarısı veren paketler onarılamasa bile VectorDB'ye sızma veya gereksiz döngüye girme riski taşıyordu.

## Decision
Sistemi "Bullet-Proof" endüstriyel standartlara getirmek için şu mekanizmalar geliştirildi:
1. **Rate Limiting:** `repair.py` içerisine Redis tabanlı `LLM_RATE_LIMIT_PER_MIN` sınırı getirildi (Varsayılan: 50 istek/dakika). Aşıldığında LLM motoru kapatılarak paketler direkt çöpe atılır.
2. **Fail-Open MCP:** `validation.py` içerisindeki MCP fetch çağrısı `try-except` bloğuna alındı. Eğer MCP çökerse, sistem hata vermek yerine "Fail-Open" politikasıyla (validation bypass edilerek) akışı serbest bırakır.
3. **Passive Monitoring:** `.env` içerisine `PASSIVE_MONITORING=true/false` bayrağı eklendi. Aktif olduğunda, SentinelCell Gateway trafiği 0ms gecikme ile anında geçirir, tüm onarım/hata loglama işlemlerini `asyncio.create_task` ile arkaplana atar.
4. **Replay Script:** `src/gateways/dlq_replay.py` yazılarak, `dlq.json` dosyası içindeki zehirli olmayan veya fazla büyük olmayan ölü paketlerin `redis_mq`'nun `sentinel.in` kuyruğuna yeniden basılması (Replay) sağlandı.
5. **Poisoning Drop:** `orchestrator.py` içindeki `decider_node` düğümü, hata içeriğinde `SECURITY_BREACH` kelimesini yakaladığı anda paketi tamir (repair) motoruna yollamadan `end` noduyla anında imha eder.

## Consequences
### Positive
- Siber saldırganlar artık LLM token bütçenizi tüketmek için DDOS yapamaz (Rate Limit kalkanı).
- MCP çökse bile ajan iletişimi kopmaz (Fail-Open).
- Gateway, Passive Monitoring sayesinde ana sistem akışına milisaniye bile etki etmeden (Sıfır Gecikme) arkaplanda güvenlik analizi yapabilir.
- Hatalı paketler veri kaybı olmadan geriye sarılabilir (DLQ Replay).

### Negative
- Passive Monitoring açıldığında bozuk veya zehirli paketler sisteme anlık olarak geçer (Asenkron tespit edilir ama engellenmez). Bu mod sadece Sniffing için uygundur, Gateway (Engelleyici) modu için kapalı tutulmalıdır.
- Fail-Open durumunda sistem schema validasyonunu kaybettiği için "Geçici Körlük" yaşayabilir.
