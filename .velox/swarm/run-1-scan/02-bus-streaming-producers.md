# bus, streaming, producers

Status: ok

Now cli.py, config, erasure, and models.

Result: Partial. I read the scope files in full except `cli.py`, which I only saw through a grep that was cut off. I never reached `config.py` or `governance/erasure.py` because the read budget ran out. Any host, port, default or erasure detail that lives there is unknown. `file:line` locators are counted by hand from reads that carried no line numbers, so treat ±2 lines as possible.

**Findings:**
- `src/eurostream/streaming.py:96` — The velocity rule `stats.count == self._velocity_threshold + 1` fires once per customer per window. It uses `==`, so later payments in the same window raise no alert. The severity is HIGH.
- `src/eurostream/streaming.py:71-73` — State is three in-memory dicts (`_windows`, `_last_seen`, `_history_by_customer`). `checkpoint()` and `restore()` exist at 162-190, but I did not see them called in the `stream` command. Unverified, because my `cli.py` grep did not search for them. If they are not called, restart loses the state. The deque is capped at 200 per customer, but the customer count is unbounded between `expire()` runs.
- `src/eurostream/streaming.py:242-243` — `expire(time.time())` runs only every 50 records and uses wall-clock time. Event-time windows (`occurred_at`) and processing-time expiry are mixed, so replaying old data expires state incorrectly.
- `src/eurostream/streaming.py:162-174` — The checkpoint docstring says "enables exactly-once recovery". The write is a plain `write_text` with no atomic rename. It is not coordinated with the offset commit, so recovery is at best at-least-once.
- `src/eurostream/streaming.py:258-270` — Alerts are produced to `fraud_alerts` before `commit()`. A crash between the two replays the payment and re-emits the alert. Alert dedup depends on the state, which is lost on restart. That makes it at-least-once with duplicate alerts.
- `src/eurostream/streaming.py:246-253` — Non-payment and malformed records are committed and dropped. There is no dead-letter topic, only a `malformed_events` counter.
- `src/eurostream/streaming.py:254-257` — Suppressed customers are skipped only on the payments path through `suppression_check`. State already held in `_history_by_customer` for an erased customer is not purged here.
- `src/eurostream/bus/sqlite.py:187-189` — `close()` calls `commit()`, which writes the in-memory `_pos`. `poll()` advances `_pos` at fetch (line 176), so a record fetched but not yet processed gets committed on close and is lost.
- `src/eurostream/bus/sqlite.py:57` — The lock is a `threading.Lock`, so it is process-local. Separate processes (`produce`, `stream`, `erasure-worker`) rely on SQLite file locking and `BEGIN IMMEDIATE` (line 100), with no busy-timeout set. Concurrent CLI processes can hit "database is locked".
- `src/eurostream/bus/sqlite.py:97` — The partition is hard-coded to 0, so there is no parallelism, and Spark partition/offset semantics do not map to it.
- `src/eurostream/bus/sqlite.py:158-166` — `poll(timeout)` ignores the timeout and returns immediately, so consumers busy-poll.
- `src/eurostream/bus/sqlite.py:12-19` — The `messages` table stores raw payloads, including PII (see the data surfaces below). I found no retention or delete path in this file. Rows are never purged, so the log is unbounded and erasure cannot reach it from here.
- `src/eurostream/bus/kafka.py:99` — `produce` returns `offset=0, partition=0` and delivery is asynchronous. Errors are only logged in `_on_delivery` (82-84), so callers cannot detect loss. `cli.py:136-137` flushes at the end of the `produce` command. The producer has no idempotence setting (`enable.idempotence` / `acks`) in its config at 61-67, so duplicates are possible on retry.
- `src/eurostream/bus/kafka.py:126` — Auto-commit is off and commit is synchronous (203). The default `auto_offset_reset` is "latest" (112).
- `src/eurostream/bus/kafka.py:157-158` — Non-EOF consumer errors are logged and the poll returns None. They are indistinguishable from an idle topic, so `idle_stop` can end a run early on a broker error.
- `src/eurostream/bus/kafka.py:73-74` — Credentials come from settings (`kafka_username`, `kafka_password`) and are stripped of quotes. No hard-coded secret was seen in the files I read. They are applied only if both username and password are set (line 68). If either is missing, the client connects with no security protocol (plaintext).
- `src/eurostream/bus/kafka.py:12-41` — `_parse_bootstrap` accepts URIs of the form `scheme://user:pass@host:port`, so a secret may sit inside the bootstrap env var. A failed match logs the first 30 characters of the string (line 40), which could leak a credential.
- `src/eurostream/producers.py:55-56, 89` — The generated events carry email and IBAN, and the click events carry IP address. These go into message payloads in plaintext through `model_dump_json()` and into the bus.
- `src/eurostream/producers.py:90` — `amount or random.uniform(5, 500)` replaces an explicit `amount=0` with a random value.
- `src/eurostream/metrics.py:15-20` — Metrics are in-memory and lost on restart. Histograms keep every observation in a list with no bound (`observe`, line 28). `flush()` appends to a JSONL file, and `render_prometheus` renders text, but I saw no HTTP server, so there is no Prometheus endpoint.

**1. Source systems:**
- Kafka (Aiven per the comment at `cli.py:43`; the engine is `confluent_kafka`):
  - Selected when `settings.event_bus_backend == "kafka"` (`cli.py:45`, `.env` var `EUROSTREAM_EVENT_BUS_BACKEND`).
  - The bootstrap env var is `EUROSTREAM_KAFKA_BOOTSTRAP_SERVERS` (`kafka.py:27`). The settings fields are `kafka_bootstrap_servers`, `kafka_username`, `kafka_password`, `kafka_security_protocol` and `kafka_sasl_mechanism` (`kafka.py` KafkaBus).
  - Code defaults are SASL_SSL and SCRAM-SHA-256 (`kafka.py:55-56`).
  - Host and port are not in code and are unknown.
- SQLite bus: `settings.data_dir / "events.db"` (`cli.py:56,58`), the default backend. It runs in WAL mode (`sqlite.py:58`) with tables `messages`, `consumer_offsets` and `broker_offsets` (12-37).
- Metrics JSONL file: `settings.metrics_path` (`cli.py:64`). No Prometheus endpoint was found.
- Faker-simulated source systems (orders, clicks, payments) in `producers.py:33-37`. Locales are de_DE, fr_FR and nl_NL (line 40).

**2. Data surfaces:**
- Topic `orders` (`producers.py:19`):
  - Producer: `OrderProducer` (about line 104).
  - Consumer: the `bronze-ingester` group (`cli.py:196`).
  - Payload fields: event_id, occurred_at, order_id, customer_id, email, iban, country, amount_eur, marketing_consent (`producers.py:50-60`), plus headers schema_version and event_type.
  - Holds PII: true (email, iban, customer_id, country).
  - Retention: none found. Erasure reaching it: null.
- Topic `clicks` (`producers.py:20`):
  - Producer: `ClickProducer`.
  - Consumer: `bronze-ingester`.
  - Payload fields: event_id, occurred_at, click_id, customer_id, session_id, ip_address, page, country (64-73).
  - Holds PII: true (ip_address, customer_id, session_id).
  - Retention: none found. Erasure reaching it: null.
- Topic `payments` (`producers.py:21`):
  - Producer: `PaymentProducer`.
  - Consumers: `fraud-stream` (`cli.py:158`) and `bronze-ingester`.
  - Payload fields: event_id, occurred_at, payment_id, order_id, customer_id, iban, amount_eur, country, merchant_country (83-93).
  - Holds PII: true (iban, customer_id).
  - Retention: none found. Erasure: the fraud stream skips suppressed customers (`streaming.py:254`), but the topic data is not erased in the files I read.
- Topic `erasure_requests` (`producers.py:22`):
  - Producer: `EventGenerator.erasure` / `cli.py` erase.
  - Consumer: the `erasure-worker` group, with earliest offset reset (`cli.py:74,84`).
  - Payload fields: event_id, occurred_at, request_id, customer_id.
  - Holds PII: true (customer_id).
  - Retention: none found. Erasure: null (not read).
- Topic `fraud_alerts` (`cli.py:162`, `streaming.py:204`):
  - Producer: `

## Findings

- `src/eurostream/streaming.py:96` — VELOCITY alert fires only when stats.count == velocity_threshold + 1, so it alerts once per window and not on later payments.
- `src/eurostream/streaming.py:71` — Fraud scorer state (_windows, _last_seen, _history_by_customer) is in-memory dicts that are lost on restart unless checkpoint()/restore() are called, and per-customer keys are unbounded between expire() runs.
- `src/eurostream/streaming.py:243` — expire() runs only every 50 records using wall-clock time.time() while windows use event-time occurred_at, mixing time domains.
- `src/eurostream/streaming.py:174` — checkpoint() docstring claims exactly-once recovery but writes state with a non-atomic write_text, uncoordinated with the offset commit.
- `src/eurostream/streaming.py:262` — Alerts are produced to fraud_alerts before consumer.commit() at the end of the loop, so a crash replays the payment and emits duplicate alerts (at-least-once).
- `src/eurostream/streaming.py:251` — Malformed events are only counted (malformed_events) and committed, with no dead-letter topic.
- `src/eurostream/bus/sqlite.py:189` — SqliteConsumer.close() commits _pos, which poll() advanced at fetch time, so a fetched but unprocessed record can be committed and lost.
- `src/eurostream/bus/sqlite.py:57` — The bus uses a process-local threading.Lock; cross-process concurrency relies on SQLite file locking with no busy timeout, risking 'database is locked'.
- `src/eurostream/bus/sqlite.py:97` — Partition is hard-coded to 0, so the SQLite bus has no partition parallelism.
- `src/eurostream/bus/sqlite.py:18` — messages table stores raw event payloads including PII with no retention or delete path, so the log grows unbounded.
- `src/eurostream/bus/kafka.py:99` — KafkaProducer.produce is async and returns a fake RecordMetadata(offset=0), with delivery errors only logged, and the producer config sets no idempotence or acks.
- `src/eurostream/bus/kafka.py:157` — Non-EOF Kafka poll errors are logged and poll returns None, indistinguishable from idle, so idle_stop can end a run early.
- `src/eurostream/bus/kafka.py:68` — SASL security settings are applied only if both username and password are set; otherwise the client connects without security.protocol.
- `src/eurostream/bus/kafka.py:40` — Bootstrap parser accepts user:pass@ URIs and logs the first 30 chars of the cleaned string on mismatch, a potential credential leak.
- `src/eurostream/producers.py:55` — Generated order and payment events put email and IBAN, and clicks put ip_address, into plaintext message payloads on the bus.
- `src/eurostream/producers.py:90` — amount or random.uniform(5, 500) replaces an explicit amount of 0 with a random value.
- `src/eurostream/metrics.py:28` — observe() appends every observation to an unbounded in-memory list; metrics are lost on restart and no Prometheus endpoint exists.
