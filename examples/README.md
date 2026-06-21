# SentinelCell Examples

Bu dizin, **SentinelCell MAS Immune System** mimarisinin yeteneklerini uygulamalı olarak anlamanızı sağlayacak canlı demolar içermektedir.

Aşağıdaki örnek scriptleri doğrudan terminalden çalıştırabilirsiniz. Çalıştırmadan önce proje dizininde olduğunuzdan ve `.env` dosyanızda ilgili LLM API anahtarlarının yapılandırıldığından emin olun. Gerekli Python yolunu (`PYTHONPATH`) ayarlamak için komutların başında `PYTHONPATH=.` bulundurmayı unutmayın.

## Örnekler

### 1. Basic Usage (`basic_usage.py`)
En temel "Hello World" tarzı kullanım senaryosudur. Kasten eksik alanlara sahip bir JSON payload'u oluşturulur ve LangGraph tabanlı `SentinelOrchestrator`'a verilir. Ajanın bu veriyi nasıl onaylamadığını (validate) ve ardından nasıl Self-Healing (kendini iyileştirme) mekanizmasıyla düzelttiğini gösterir.
```bash
PYTHONPATH=. python examples/basic_usage.py
```

### 2. Multi-Agent Flow (`multi_agent_flow.py`)
Klasik bir Producer-Consumer (Üretici-Tüketici) modeli üzerinde SentinelCell'in bir ara katman (middleware/bağışıklık sistemi) olarak nasıl çalıştığını gösterir.
Üretici hatalı veri gönderir; tüketici ise sadece temiz veri kabul etmektedir. SentinelCell araya girer, onarımı sağlar ve tüketiciye temiz veriyi ulaştırır.
```bash
PYTHONPATH=. python examples/multi_agent_flow.py
```

### 3. Custom Skill Demo (`custom_skill_demo.py`)
SentinelCell'in üzerine nasıl özel bir "Skill" (Yetenek) node'u inşa edilebileceğini gösterir. Bu örnekte, şifre içeren hassas bir payload'u algılayıp şifreleri "******" olarak maskeleyen bir `Sanitizer` (Temizleyici) node'unun LangGraph state machine'ine nasıl eklendiği kurgulanmıştır.
```bash
PYTHONPATH=. python examples/custom_skill_demo.py
```
