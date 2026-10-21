# Bằng chứng audit được lưu cùng kế hoạch

Các JSON nhỏ được sao chép nguyên trạng từ artifacts đã tồn tại ngày 21/10/2026. Đây là audit/provenance, **không phải final benchmark results**. Không chứa raw datasets, embeddings hoặc user-level data.

| File | Artifact gốc tương đối repository | Nội dung |
|---|---|---|
| [acquisition-eswiki-2018.json](acquisition-eswiki-2018.json) | `data/raw/eswiki/manifest-v2.json` | URL, bytes, local SHA256, upstream checksum nếu có, license, verification timestamp |
| [preparation-study-v2.json](preparation-study-v2.json) | `data/processed/study-v2/manifest.json` | Config, input/output hashes, mapping/graph/sample counts, training attrition, preparation time |
| [validation-april-2018.json](validation-april-2018.json) | `results/study-v1/validation_audit.json` | April schema/min-count and attrition audit; không có ranking accuracy |

Không sửa những bản sao này để khớp một run mới; tạo version/file khác khi thực sự rerun. Local SHA256 chứng minh fingerprint của bytes đã đọc, không tự chứng minh tính xác thực của publisher. Acquisition có checksum May/June bytes nhưng không có parsed test labels; việc xác minh hash khác việc mở labels để tuning.

Prepared graph hashes chỉ chứng minh artifacts của policy đã mô tả. Chúng không chứng minh redirect history hoàn hảo, labels đầy đủ, graph không thiếu template links hoặc sample đại diện toàn Wikipedia. Các giới hạn đó nằm trong [DATA_AUDIT](../DATA_AUDIT.md).
