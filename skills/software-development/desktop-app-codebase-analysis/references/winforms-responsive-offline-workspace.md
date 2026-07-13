# Responsive offline workspace for legacy WinForms

Use this pattern when a fixed-canvas industrial/HMI form becomes unusable at full screen and the deliverable is an offline demonstrator rather than restoration of every unfinished production page.

## Diagnosis

- Read both `Form*.Designer.cs` and runtime-created controls.
- Trace the active hierarchy from `Form` to the actual module. Fixed `Location`/`Size` anywhere in that path can leave controls clustered in the upper-left.
- Distinguish implemented modules from designer-only tabs and placeholders.

## Repair pattern

1. Call a small runtime layout method immediately after `InitializeComponent()`.
2. Maximize the HMI form and set a practical minimum size.
3. Hide the unfinished fixed-coordinate production header/pages in offline demo mode when they add no working behavior.
4. Make the active chain fill the client area:
   - content panel: `DockStyle.Fill`
   - tab control: `DockStyle.Fill`
   - active tab/module root: `DockStyle.Fill`
5. If this is a single-purpose demo, clear inactive tabs and add/select only the working offline tab.
6. Replace a full-width `FlowLayoutPanel` toolbar with a four-column `TableLayoutPanel`:
   - fixed label width
   - percent-width model selector
   - fixed start button
   - fixed stop button
7. Use percentage rows for result list and log output.
8. On `ListView.Resize`, preserve narrow fixed columns and divide remaining `ClientSize.Width` between descriptive columns.

## Verification checklist

- Run a real Windows `dotnet build` for the Windows-targeted project.
- Use an OS-safe temporary `hermes-verify-*` script for focused assertions such as:
  - legacy demo-incompatible panel hidden
  - only intended workspace selected
  - complete active container chain uses `DockStyle.Fill`
  - toolbar includes a percent-width selector column
  - list columns subscribe to resize behavior
- Clean up the temporary verifier.
- Report these checks as **ad-hoc verification**, not full-suite success.
- Whenever possible, log in and visually inspect at two window sizes. Compilation and source assertions do not prove good composition.

## Common failed approach

Maximizing the form and docking only the first parent panel can make the window larger while leaving all descendants at their designer coordinates. The symptom remains “everything is squeezed into the upper-left.” Repair the whole active hierarchy or replace the affected module with responsive containers.
