---
name: desktop-app-codebase-analysis
description: Analyze local desktop application codebases, especially Windows/.NET WinForms/WPF projects with databases, installers, binaries, and hardware/industrial integrations. Use when the user asks to parse/understand an upper-computer/HMI/desktop app folder rather than simply count LOC.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, wsl]
metadata:
  hermes:
    tags: [desktop-app, winforms, wpf, dotnet, access, hmi, code-analysis]
    related_skills: [codebase-inspection, systematic-debugging]
---

# Desktop App Codebase Analysis

Use this for local desktop app folders where the deliverable is an explanatory reverse/architecture analysis: technology stack, entry points, runtime artifacts, databases/configuration, UI flows, protocols, dependencies, build/run status, and missing pieces.

## Trigger

- User asks to “解析一下这个上位机软件”, “analyze this desktop app”, “what does this WinForms/WPF app do?”, “understand this HMI/upper-computer software”, or points to a Windows project/output folder.
- Folder contains `.sln`, `.csproj`, `.vbproj`, `.exe`, `.dll`, `.mdb/.accdb`, `.config`, `bin/`, `obj/`, installers, or vendor hardware DLLs.

## Workflow

1. **Translate paths and inventory safely**
   - In WSL, translate `C:\Users\...` to `/mnt/c/Users/...` for file inspection.
   - List files with `search_files(target='files')`; note nested project folders, `.vs`, `bin`, `obj`, `Debug`, `Release`.
   - Separate source files from generated/build artifacts.

2. **Identify stack and entry points**
   - Read solution/project files (`.sln`, `.csproj`, `.vbproj`) and startup files (`Program.cs`, `App.xaml`, `MainWindow`, `Form*`).
   - Extract target framework, output type, UI framework, package references, and runtime dependencies.
   - For .NET desktop apps, inspect `*.deps.json` and `*.runtimeconfig.json` in `bin/...` to confirm actual deployed dependencies.

3. **Read UI and behavior together**
   - Read both code-behind and designer/XAML files.
   - Designer files often reveal the real product domain through menu labels, tabs, button text, and hidden controls even when code-behind is empty.
   - Summarize screens and workflows from labels/menu structure, but distinguish implemented logic from UI-only stubs.

4. **Inspect embedded/local databases and configs**
   - Look for `.mdb/.accdb/.sqlite/.db/.json/.xml/.ini/.config` under both source and `bin` output.
   - For Access `.mdb/.accdb` on Windows/WSL, use Windows PowerShell + OleDb when available to list tables, row counts, schemas, and representative rows. See `references/access-mdb-ole-db-export.md`.
   - Treat databases as part of the application logic: they may contain test methods, scripts, device addresses, credentials, model lists, and process recipes.

5. **Find communications and hardware integration**
   - Search source and database/config text for protocol/device terms: `PLC`, `HslCommunication`, `Modbus`, `SerialPort`, `Socket`, `TcpClient`, `COM`, `IP`, `VISION`, `MES`, `SCAN`, `OleDb`, vendor DLL/class names.
   - For industrial/HMI software, map each observed protocol to evidence: code call, package reference, database method name, IP/port, PLC address, or script body.

6. **Verify build/run state when possible**
   - If it is a code project and toolchain exists, run a real build (`dotnet.exe build` for Windows-targeted .NET from WSL is often better than Linux `dotnet`).
   - Report exact success/failure, warning count, and key warnings. Do not imply runtime success from build success.
   - For WinForms layout changes, compilation is only structural evidence. Verify the post-login/main window—not merely the login dialog—and distinguish source assertions, process responsiveness, window-state checks, and actual visual inspection.
   - When no canonical UI test exists, create a focused ad-hoc verifier under an OS-safe temporary path named with a `hermes-verify-` prefix. It may assert responsive-layout invariants (for example, `WindowState = Maximized`, content container and tab control using `DockStyle.Fill`, and a sane `MinimumSize`) and run the Windows build. Clean it up afterward and report it explicitly as **ad-hoc verification**, not “the test suite is green.”

7. **Repair fixed-canvas WinForms layouts end-to-end**
   - Designer-generated forms often encode one development resolution through fixed `ClientSize`, fixed-height content panels, and child controls with explicit `Location`/`Size`.
   - Preserve fixed top headers with `DockStyle.Top`, but set the complete active container chain (`Panel` → `TabControl` → `TabPage` → module root) to `DockStyle.Fill`. Maximizing the form or docking only the outer panel is not enough.
   - For an offline/demo runtime, prefer one clean, functional workspace over exposing unfinished production tabs and absolute-positioned placeholders. Hide/remove stubs in demo mode without implying those production modules are complete.
   - Rebuild full-width command bars with `TableLayoutPanel`: fixed columns for labels/actions and a percent-width column for the main selector. Avoid `FlowLayoutPanel + AutoSize` when consistent full-width alignment is required.
   - Use percentage rows for primary list/log splits. Resize flexible `ListView` columns from `ClientSize.Width`, while keeping order/status columns fixed.
   - Set a practical `MinimumSize`; use `WindowState = Maximized` for full-screen HMI workflows. Prefer a small runtime layout method called immediately after `InitializeComponent()` over broad edits to generated designer code.
   - Do not add `AnchorStyles.Right` to fixed-position inputs/buttons without checking overlap at narrow widths. Anchor only controls whose geometry can safely stretch.
   - A responsive main form does not prove nested legacy pages are responsive. Inspect each important page and settings form separately when the user expects the whole application to scale.
   - See `references/winforms-responsive-offline-workspace.md` for an implementation and verification checklist.

8. **Report with confidence boundaries**
   - Clearly separate:
     - “Implemented in source”
     - “Configured in database/config”
     - “Referenced but missing/not wired”
     - “Inferred from labels/data”
   - Call out security issues such as plaintext credentials, incorrect login checks, executable scripts in databases, unencrypted local DBs, and hardcoded network endpoints.

## Access MDB extraction via PowerShell OleDb

When `mdbtools` is unavailable or would require sudo, try Windows PowerShell from WSL if Windows has the ACE/Jet provider. Minimal pattern:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(wslpath -w /tmp/export_mdb.ps1)" -DbPath 'C:\path\to\Setting.mdb'
```

Keep script output concise: table names, row counts, schema, first 20 rows for important tables, distinct method/type columns, and any script/config fields. Avoid dumping huge script blobs into the final answer unless needed.

## Pitfalls

- **COUNT(*) login bug:** In Access/OleDb login code, `ExecuteScalar()` on `SELECT COUNT(*) ...` returns `0`, not `null`, for failed login. Checking only `result != null` makes wrong passwords pass. Require `Convert.ToInt32(result) > 0`.
- **UI exists ≠ feature implemented:** WinForms designer files may contain full menus for MES/PLC/logs/settings while code-behind handlers are empty or commented out. State this explicitly.
- **Database scripts may reference missing host APIs:** Access tables can hold C# script bodies that depend on vendor DLLs or host globals absent from the current repo. Treat them as configuration evidence, not working source, until dependencies and host interfaces exist.
- **Windows-targeted .NET from WSL:** For `net*-windows` WinForms/WPF projects, prefer `dotnet.exe build 'C:\...\app.sln'` to verify against the Windows Desktop runtime.

## Reporting template

Use concise Chinese when the user asks in Chinese:

```markdown
## 结论
一句话定位：...

## 技术栈/结构
- ...

## 功能模块
- 主界面：...
- 设置界面：...
- 数据库配置：...

## 通信/硬件/数据库
- PLC: evidence
- 视觉: evidence
- Modbus/串口: evidence

## 完成度和风险
- 已实现：...
- 未接上/缺失：...
- 安全问题：...

## 验证结果
- build/run command + real result

## 下一步建议
1. ...
```

## References

- `references/access-mdb-ole-db-export.md` — PowerShell OleDb snippets for inspecting Access `.mdb/.accdb` from WSL/Windows.
- `references/winforms-responsive-offline-workspace.md` — end-to-end pattern for replacing fixed-canvas demo layouts with a responsive single workspace.