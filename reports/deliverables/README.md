# Bộ slide IT4868E

[Wikipedia_Navigation_IT4868E.pptx](Wikipedia_Navigation_IT4868E.pptx) gồm10slides,4native charts,4native tables và10speaker notes. Mạch nội dung theo [PRESENTATION](../PRESENTATION.md), đọc cùng [REPORT](../REPORT.md). Time budget12–14phút, chưa phải thời lượng đo qua một cuộc bảo vệ thử.

## Kiểm tra đã thực hiện

- Render và đọc từng trang của **file PPTX cuối cùng sau import lại**, gồm chữ tiếng Việt, wrapping, bố cục và data labels. [PNG previews](previews/) là evidence trực quan.
- Package/relationships, slide count/geometry, Arial font policy, native chart owners và embedded workbook/cache references đều pass. [Validation receipt](validation.json) ghi phạm vi từng check.
- [Source data](source-data.json) giữ hashes và giá trị từ frozen artifacts. Chart workbook snapshot làm tròn tối đa8chữ số thập phân để tương thích numeric precision của Excel; hiển thị4chữ số cho ranking scores. Report/CSV giữ precision gốc.
- `python3 scripts/verify_presentation.py` kiểm tra10slides,4charts,10notes, file hashes và chart values đối chiếu nguồn. Không train model.

Không mở/chỉnh sửa/lưu lại file bằng native PowerPoint hay Google Slides trong môi trường này. Rendering/OOXML checks không thay compatibility test trong ứng dụng đích. Bảng ởslides2/5/6/9 là bảng phương pháp/protocol, không có arithmetic totals cần kiểm tra; không nhận đã “verify totals” khi checker bỏ qua.

## Tái tạo tùy chọn

Hai script `scripts/presentation_data.py` và `scripts/build_presentation.mjs` tạo deck, không dùng Python-pptx. Runtime authoring là `@oai/artifact-tool`2.8.106 và helpers của Presentations skill26.1025.11240; đây là dependency tùy chọn của môi trường authoring, không phải dependency của pipeline nghiên cứu hoặc yêu cầu để mở PPTX.

```sh
python3 scripts/presentation_data.py
# Trỏ các biến sau vào runtime/skill được cài trên máy hiện tại:
# ARTIFACT_MODULES: thư mục node_modules có @oai/artifact-tool
# RUNTIME_NODE_MODULES: cùng thư mục node_modules
# PRESENTATION_SKILL_DIR: thư mục skill có container_tools
# RUNTIME_PYTHON: Python có lxml cho validators
# PRESENTATION_OUTPUT: tên file .pptx mới trong repository, parent directory đã tồn tại
node scripts/build_presentation.mjs
```

Finalizer từ chối overwrite file đã có. Giữ source deck cũ, chọn output mới nếu dựng một revision; không sửa binary bằng tay. Node runtime dùng ở lượt tạo này:24.22.1, fontArial. Manifest ghi bản hiện hành để kiểm tra integrity, không cam kết binary PPTX deterministic qua các lần export.

## Rehearsal demo còn lại

HTML demo là artifact khác với deck. CUA ngày05/11/2026 bị saved permission chặn origin localhost, nên chưa xác nhận browser visual/interaction QA. Người trình bày tự mở `reports/generated/demo.html` và đi qua Danza posmoderna / Tragacete theo [kịch bản](../PRESENTATION.md). Có bảng [CASE_STUDIES](../CASE_STUDIES.md) dự phòng. Không claim đã thực hiện human rehearsal, native Office testing hoặc human extraction adjudication.
