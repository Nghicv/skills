# Skills bên thứ ba

Các skills cài từ nguồn ngoài, **không vendor vào repo này** (để còn nhận cập
nhật từ upstream — xem lý do trong
[docs/specs/2026-07-31-skills-repo-design.md](docs/specs/2026-07-31-skills-repo-design.md)).
Chúng nằm trực tiếp trong `~/.claude/skills` / `~/.agents/skills`;
`scripts/install.sh` tự động bỏ qua (không quản lý entry không phải symlink vào
repo).

Máy mới: chạy `scripts/install.sh` cho skills của repo, rồi cài lại danh sách
dưới đây (đa số qua [skills.sh](https://skills.sh): `npx skills add <source>`).

| Skill | Nguồn | Ghi chú |
|---|---|---|
| agp-9-upgrade | Google — bộ Android skills chính thức | |
| android-cli | Google — bộ Android skills chính thức | |
| edge-to-edge | Google — bộ Android skills chính thức | |
| gma-android-migrate-to-next-gen | Google — bộ Android skills chính thức | chỉ đang có ở `~/.claude/skills` |
| migrate-xml-views-to-jetpack-compose | Google — bộ Android skills chính thức | |
| navigation-3 | Google — bộ Android skills chính thức | |
| play-billing-library-version-upgrade | Google — bộ Android skills chính thức | |
| r8-analyzer | Google — bộ Android skills chính thức | |
| find-skills | skills.sh (Vercel Labs) | |
| vercel-react-best-practices | vercel-labs/agent-skills | |
| vercel-composition-patterns | vercel-labs/agent-skills | **thiếu SKILL.md** — cài lại hoặc xóa |
| vercel-react-native-skills | vercel-labs/agent-skills | **thiếu SKILL.md** — cài lại hoặc xóa |
| web-design-guidelines | Vercel — Web Interface Guidelines | |
| app-store-screenshots | *chưa xác nhận* | có thể là tự viết → nếu đúng thì move vào `skills/ios/` |

> Khi cài mới hoặc gỡ một skill bên thứ ba, cập nhật bảng này.
