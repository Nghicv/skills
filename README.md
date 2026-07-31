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
scripts/install.sh            # symlink toàn bộ skills vào cả 2 harness
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

## Mục lục skills

> Chưa có skill nào — sẽ được cập nhật khi migrate các skills hiện có về repo.

### android

### ios

### mobile

### backend

### frontend

### workflow

### tools
