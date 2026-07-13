# opoerss Project UI Map

> **Status: provisional source snapshot, not the historical or production UI specification.** The available source is incomplete, and the current layout differs from the version previously used. Update this map whenever real operating-scene evidence, confirmed historical screenshots, device behavior, or a more complete source package becomes available. In any conflict, confirmed现场 behavior wins.

## Live location

```text
Windows: C:\Users\LYH\Desktop\opoerss\opoerss
WSL:     /mnt/c/Users/LYH/Desktop/opoerss/opoerss
Solution: opoerss.sln
Project:  opoerss/opoerss.csproj
```

The current project targets `.NET 6 Windows Forms` with nullable reference types enabled. Build with Windows `dotnet` because runtime UI and OleDb are Windows-specific.

## Primary UI files

| Surface | Static layout | Runtime behavior |
|---|---|---|
| Main/production window | `opoerss/Form1.Designer.cs` | `opoerss/Form1.cs` |
| Settings window | `opoerss/FormSetting.Designer.cs` | `opoerss/FormSetting.cs` |
| Login dialog | `opoerss/frmLogin.Designer.cs` | `opoerss/frmLogin.cs` |
| Startup/login flow | — | `opoerss/Program.cs` |
| Session/permissions | — | `opoerss/UserSession.cs` |
| Offline simulator behavior | — | `DetectionModels.cs`, `OfflineSimulation.cs` |
| Data shown in forms | — | `AccessRepository.cs` |

Do not include or repeat account names, passwords, connection secrets, or database contents in UI documentation or screenshots.

## Main form invariants

Current live structure:

```text
Form1
├─ menuStrip1                  top menu
├─ panel9                      production visualization/status header; Dock=Top
└─ panel12                     content region; runtime Dock=Fill
   └─ tabControl1              runtime Dock=Fill
      ├─ 检测 and production tabs
      └─ tabCtrlPanel / 面板
         └─ runtime offline simulation layout
```

`Form1.ConfigureResponsiveLayout()` currently:

- centers startup;
- sets `MinimumSize = 1024 × 700`;
- maximizes the window;
- keeps `panel9.Visible = true`;
- changes `panel12` and `tabControl1` to `DockStyle.Fill`;
- preserves every existing business tab.

These are preservation invariants. Do not hide the header or clear tabs as a shortcut.

## Offline simulation layout

`Form1.InitializeOfflineSimulation()` owns runtime controls and replaces only the contents of `tabCtrlPanel`:

```text
GroupBox (Fill)
└─ TableLayoutPanel: 1 column, 3 rows
   ├─ toolbar: absolute label/buttons + percentage ComboBox
   ├─ ListView: 60%
   └─ RichTextBox log: 40%
```

The five ListView columns are `顺序`, `检测项`, `方法`, `结果`, and `说明`. `ResizeStepColumns()` keeps the name and description columns flexible. Any change must preserve readable result states and safe cancellation behavior.

## Settings form facts

`FormSetting` is currently explicitly read-only in the offline simulation version:

- Data grids load parameters, parts, and test items.
- Buttons are disabled and labeled `（只读）`.
- The title communicates that writes are unsupported.

The Designer still uses many fixed positions. Improve responsiveness without pretending disabled save/delete/copy operations work. Data grids should remain visible, scrollable, and associated with the correct tab or detail region.

## Login form facts

`frmLogin` is a fixed-size dialog in the Designer (`619 × 439`, `AutoScaleMode.Font`). It supports:

- username selection;
- password entry;
- show/hide password;
- Enter via `AcceptButton`;
- Cancel via `CancelButton`;
- database error and invalid-login messages.

UI changes must preserve keyboard flow, password masking, error visibility, and modal semantics. The user enters credentials; automation must never type or store them.

## Generated output

`bin/` and `obj/` are generated. Builds frequently dirty tracked output files in this repository. Before committing a source fix:

1. inspect `git status --short`;
2. preserve intentional `.cs`, `.csproj`, JSON, Markdown, or database changes;
3. restore only generated churn after confirming scope;
4. run `git diff --check`.

Do not use broad cleanup commands that can delete untracked user work.
