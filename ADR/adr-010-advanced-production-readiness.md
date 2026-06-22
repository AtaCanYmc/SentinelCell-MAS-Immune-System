# ADR 010: Advanced Production-Readiness (DLQ, Async I/O & Rate Limits)

## Status
Accepted

## Context
Projenin kurumsal standartlarda bir Gateway / Middleware olarak konumlandırılması, yüksek trafik altındaki darboğazları (bottleneck) ve potansiyel maliyet kayıplarını yönetmeyi zorunlu kılmıştır:
1. **Async I/O (Bloklanma):** SentinelOrchestrator LangGraph düğümleri çalışırken, `log_to_vectordb` düğümü eşzamanlı (synchronous) çalışıyordu. Veritabanında yaşanacak herhangi bir gecikme ana akışı durduruyordu.
2. **DLQ Eksikliği:** Kurtarılamayan veya reddedilen paketler (dropped packets) konsola yazdırıldıktan sonra sonsuza dek kayboluyordu. Oysa bu paketler bir "Ölü Mektup Kuyruğu" (Dead Letter Queue - DLQ) içerisinde analiz edilmeliydi.
3. **Maliyet ve Boyut Sınırları:** Sınırsız boyuttaki bozuk JSON verilerinin onarım için LLM'e (Large Language Model) gönderilmesi, token bazlı çalışan sağlayıcılarda devasa faturalara veya Rate Limit engellemelerine yol açıyordu.
4. **Prompt Sınır İhlali (Bypass):** Prompt Injection savunması için koyduğumuz `---END UNTRUSTED DATA---` etiketinin kendisini taşıyan bir zararlı payload, LLM'e sızabilirdi.
5. **Circuit Breaker Metrikleri:** Karantina durumunun Redis'te tutulması yetersizdi; aynı zamanda Grafana ekranlarında alarm kurulabilmesi için dışarı aktarılmalıydı.

## Decision
Sistemi yüksek trafiğe (high-load) karşı dayanıklı hale getirmek için:
1. **Async I/O:** `log_to_vectordb_node` içerisindeki log yazma işlemi, Event Loop bloke edilmesin diye `asyncio.get_event_loop().run_in_executor()` kullanılarak "fire-and-forget" arka plan iş parçacığına taşındı.
2. **DLQ (Dead Letter Queue):** Reddedilen ve boyutu çok büyük olan tüm paketler için `_log_to_dlq()` yardımcı metodu yazılarak hatalar `.antigravity/logs/dlq.json` dosyasına yazılmaya başlandı.
3. **Max Payload Size:** `orchestrator.py` içerisine 10.000 karakterlik `MAX_PAYLOAD_SIZE` (ortam değişkeni destekli) limiti eklendi. Sınırı aşan paketler LLM'e gitmeden doğrudan DLQ'ya atılarak maliyet koruması sağlandı.
4. **Prompt Sanitization:** `repair.py` içerisinde, ham verinin içindeki `---START UNTRUSTED DATA---` veya `END` tagleri `[REDACTED_BOUNDARY]` olarak değiştirildi (sanitizasyon) ve prompt boundary bypass engellendi.
5. **Gauge Metriği:** Karantina durumu için `sentinelcell_quarantine_status` Gauge metriği oluşturularak, anlık `1.0` (karantinada) veya `0.0` (sağlıklı) durumu Prometheus'a açıldı.
6. **Python GIL Notu:** Python tabanlı Middleware/Gateway kullanımının çok yüksek trafikte Global Interpreter Lock (GIL) yüzünden yavaşlayabileceği gerçeği kayıt altına alındı. Bu nedenle Gateway arkasındaki servislerin pasif sniffing moduna veya rust tabanlı bir load balancer önüne alınması ileride (V2) değerlendirilecektir.

## Consequences
### Positive
- **Yüksek Performans:** VectorDB veritabanı yavaşlasa bile ana paket trafiği asla yavaşlamaz (Non-blocking I/O).
- **Maliyet Kontrolü:** Sınırsız token tüketimi ve gereksiz LLM çağrıları tamamen durduruldu.
- **Kayıpsız Analiz:** DLQ sayesinde reddedilen paketler üzerinde sonradan siber tehdit analizi yapılabilir.
- **Görsel Alarmlar:** Grafana'da büyük kırmızı karantina uyarıları eklenebilir.

### Negative
- **Olası Veri Kaybı:** "Fire-and-forget" log mekanizmasında VectorDB anlık kapalıysa loglar sessizce kaybolabilir (akışı korumak adına bu risk göze alınmıştır).
