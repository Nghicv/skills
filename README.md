# skills

Kho tổng hợp Agent Skills cá nhân cho phát triển sản phẩm — dùng chung cho
**Claude Code** và **Codex** (và mọi harness theo chuẩn
[Agent Skills](https://agentskills.io/specification)).

Đây là **nguồn chuẩn duy nhất**: mỗi skill viết một lần tại đây, symlink ra
`~/.claude/skills` (Claude Code) và `~/.agents/skills` (Codex, Copilot CLI,
Gemini CLI). Sửa skill trong repo là mọi tool nhận ngay, `git pull` là đủ để
cập nhật.

## Cài đặt

```bash
scripts/install.sh            # symlink toàn bộ skills vào cả 2 harness,
                              # đồng thời dọn link của skill đã xóa/đổi tên
scripts/install.sh --dry-run  # xem trước, không ghi gì
scripts/install.sh --force    # thay thế cả entry cũ không do repo quản lý
```

## Cấu trúc

```
skills/<domain>/<skill-name>/SKILL.md   # mỗi skill một thư mục
deprecated/                             # skill ngừng dùng (không được link)
templates/skill-template/               # khung chuẩn để tạo skill mới
skills.schema.json                      # contract frontmatter
scripts/                                # install / validate / list
THIRD-PARTY.md                          # manifest skills cài từ nguồn ngoài
docs/specs/                             # tài liệu thiết kế
```

Domain: `android` · `ios` · `mobile` (cross-platform) · `backend` · `frontend`
· `workflow` (quy trình: quick-fix, investigate-bug…) · `tools`.

Tên skill phải **duy nhất toàn repo** (khi cài sẽ flatten, bỏ cấp domain).
Skill chỉ dành cho một tool: đặt file marker rỗng `.claude-only` hoặc
`.codex-only` trong thư mục skill.

## Thêm skill mới

1. Copy `templates/skill-template/` vào `skills/<domain>/<tên-skill>/`.
2. Viết `description` bắt đầu bằng "Use when...", chỉ mô tả *khi nào dùng*
   (trigger, triệu chứng, từ khóa — có thể kèm tiếng Việt), không tóm tắt
   workflow.
3. Chạy `scripts/validate.sh` cho tới khi pass.
4. Thêm skill vào mục lục dưới đây, rồi chạy `scripts/install.sh`.

Quy ước chi tiết cho agent: xem [AGENTS.md](AGENTS.md).

Skills cài từ nguồn ngoài (Google Android skills, Vercel…) **không** nằm trong
repo này — xem danh sách và cách cài lại ở [THIRD-PARTY.md](THIRD-PARTY.md).

## Mục lục skills

### mobile

- [`aso`](skills/mobile/aso/SKILL.md) — App Store Optimization iOS + Android: nghiên cứu keyword, version hoá metadata đa locale, đo ranking, chẩn đoán tụt hạng.
- [`pytorch-to-tflite`](skills/mobile/pytorch-to-tflite/SKILL.md) — convert model PyTorch/HuggingFace sang TFLite cho Android: quantise, host, verify trên device.

### workflow

- [`investigate-bug`](skills/workflow/investigate-bug/SKILL.md) — điều tra bug tới root cause có bằng chứng, đề xuất fix nhưng chờ duyệt trước khi sửa code.
- [`quick-fix`](skills/workflow/quick-fix/SKILL.md) — fix nhanh gọn cho bug nhỏ/đã hiểu rõ, bỏ qua TDD và planning nhiều bước.
- [`provide-info`](skills/workflow/provide-info/SKILL.md) — trả lời/giải thích về codebase ở chế độ read-only, không sửa code.

### tools

- [`reddit-fetch`](skills/tools/reddit-fetch/SKILL.md) — fetch nội dung Reddit qua Gemini CLI hoặc curl JSON API khi bị 403/block.
- [`git-timesheet`](skills/tools/git-timesheet/SKILL.md) — điền file timesheet / % effort theo dự án từ commit trong GitHub org, append vào .xlsx không làm hỏng workbook.
- [`skill-config`](skills/tools/skill-config/SKILL.md) — bật/tắt/liệt kê Claude Code skills theo nhóm và scope. *(`.claude-only`)*

### android · ios · backend · frontend

*(trống — chờ skill mới)*
