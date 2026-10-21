# Bằng chứng dữ liệu, backend và final verification

Các JSON nhỏ lưu audit/provenance, không raw datasets hoặc individual user logs. Final benchmark artifacts nằm trong [reports/generated](../../reports/generated/); không coi audit counts là ranking results.

| Evidence | Nội dung |
|---|---|
| [acquisition-eswiki-2018](acquisition-eswiki-2018.json) |9URLs,bytes,SHA256,upstream checksums/license |
| [preparation-study-v2](preparation-study-v2.json) | Canonicalization,training attrition,sampling,graph counts và prepared hashes; v2 là data version dùng cho final study-v3 |
| [validation-april-2018](validation-april-2018.json) | April schema/mapping audit từ lần chuẩn bị trước; không final test accuracy |
| [preparation-replay](preparation-replay.json) | Fresh preprocessing cùng raw files:4 Parquet hashes/full counters identical |
| [gensim-build-wnm2](gensim-build-wnm2.json) | Pinned source hashes,build tools,wheel fingerprint; final native backend |
| [embedding-backend-smoke-wnm2](embedding-backend-smoke-wnm2.json) | Real training graph finite vectors/loss,negative-dot smoke; không test tuning |
| [final-runtime](final-runtime.json) | Platform/dependencies,245s model run,RSS và measurement limitations |
| [final-verification](final-verification.json) | Frozen algorithm bytes/signature check,72 tests,5600 portable re-evaluations,CI reference,browser QA limitation |

wnm1 evidence nếu có được giữ như lịch sử, **không** chứng nhận backend final. Run history và frozen policy nằm trong [RUN_PROTOCOL](../RUN_PROTOCOL.md).

SHA256 xác định bytes; checksum không tự chứng minh mọi mapping/graph label đều đúng. Query candidates giữ đầy đủ nhưng intermediate boundary loss lớn; redirects/title moves và exposure/suppression vẫn là limitations. Future raw-file checksum verification khác việc parse test labels để tuning.
