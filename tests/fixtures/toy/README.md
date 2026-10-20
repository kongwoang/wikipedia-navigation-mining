# Synthetic fixture

Đây là dữ liệu tự tạo để kiểm thử, **không phải sample từ Wikipedia**.

Graph có directed cycle A↔B, C→A, cold source E, dangling D, isolated F.
Hyperlink A→E không có published training count. Training pair B→E nằm ngoài
hyperlink support. Test có out-of-candidate B→C, out-of-vocabulary
`New_article`, và nguồn D không có candidates. F không có observable test labels.

Counts ≥11 để đi qua production Clickstream schema checks; metric unit tests
riêng sử dụng counts nhỏ hơn để tính tay. File validation tồn tại nhưng smoke
pipeline **không tuning**. Mọi score tạo ra chỉ là correctness diagnostics.
