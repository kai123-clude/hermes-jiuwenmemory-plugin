# opoerss UI Acceptance Matrix

> This is a verification framework, not a statement that the current source layout is correct. Before marking a change as production-correct, obtain a real operating-scene baseline or explicit user/现场人员 confirmation. Label screenshots as `现场已确认`, `用户已确认`, `历史参考`, `当前源码`, or `离线仿真`.

Use this checklist for before/after screenshots and runtime verification. Mark an item `N/A` only with a reason.

## Global

- [ ] No controls overlap or collapse into the upper-left corner.
- [ ] No Chinese label, button text, grid header, status text, or tab caption is clipped.
- [ ] No unexpected horizontal scrollbar appears in the main structural containers.
- [ ] Spacing is consistent within each region; `Margin` and `Padding` do not compound into large gaps.
- [ ] Keyboard focus order is logical on login/settings forms.
- [ ] Colors and text preserve OK/NG, running/stopped, connected/disconnected, and enabled/read-only distinctions.
- [ ] Closing or resizing a form does not cause disposed-control update exceptions.
- [ ] Existing production functions are not removed to improve appearance.

## Resolution and resize matrix

When practical, check:

| Case | Expected result |
|---|---|
| 1024×700 minimum | Main action areas remain reachable; labels and primary buttons are readable |
| 1366×768 | No content collision; production header and tabs remain visible |
| 1920×1080 | Flexible regions consume space without excessive blank fixed canvases |
| maximized | `panel12`/tabs fill remaining area below the production header |
| restored and resized | controls track their containers without flicker or overlap |
| 100% DPI | baseline |
| 125% DPI | no label/button clipping |
| 150% DPI | critical controls remain visible or scrollable |

Do not change system DPI without user approval. If unavailable, report untested cases explicitly.

## Main production form

- [ ] `panel9` is visible and retains production visualization/status content.
- [ ] Menu strip remains reachable.
- [ ] Every original business tab remains present.
- [ ] `panel12` fills below the header rather than using a stale fixed height.
- [ ] `tabControl1` fills its container.
- [ ] Tab content is not hidden behind the header or menu.
- [ ] Production status labels and buttons retain their intended hierarchy.
- [ ] The offline simulator remains in the `面板` tab unless navigation was explicitly redesigned.

## Offline simulation tab

- [ ] Part selector expands with the toolbar.
- [ ] Start and Stop buttons have stable widths and do not overlap.
- [ ] Start/Stop enabled states match idle/running/cancelling behavior.
- [ ] Step list shows sequence, item, method, result, and explanation.
- [ ] Flexible columns use available width; important text is not reduced to unusable widths.
- [ ] Pass/fail state remains distinguishable without relying on color alone where possible.
- [ ] Log area is readable, scrollable, and receives progress without blocking UI input.
- [ ] Stopping a run does not leave controls permanently disabled.

## Settings form

- [ ] Read-only status is visible in the title or prominent explanatory text.
- [ ] Unsupported write buttons remain disabled and are not styled as active primary actions.
- [ ] Data grids fill their intended regions and can scroll.
- [ ] Grid headers remain legible at tested DPI.
- [ ] SplitContainer panels have usable minimum sizes.
- [ ] Detail labels remain associated with their fields after resize.
- [ ] Tabs do not reveal detached or overlapping controls from another tab.
- [ ] No layout change implies data was saved when write support is unavailable.

## Login dialog

- [ ] Username, password, show-password, Login, and Cancel controls are visible.
- [ ] Password is masked by default.
- [ ] Show-password changes only visibility, not stored value.
- [ ] Enter activates Login; Escape/Cancel closes without authentication.
- [ ] Error messages are readable and do not expose entered passwords.
- [ ] Form remains centered and usable at supported DPI.
- [ ] Automation does not type, capture, or persist credentials.

## Evidence required

For a visual fix, retain or report:

1. Baseline screenshot path and reproduction state.
2. After screenshot at the same size/state.
3. Additional size/DPI screenshots that were practical.
4. Source diff for the affected layout rule.
5. Windows `dotnet build` result with zero errors.
6. Focused ad-hoc invariant check when no canonical UI test exists.
7. Explicit list of untested states or blocked screens.

A build alone is insufficient. A screenshot alone is insufficient if the source no longer builds or functionality was hidden.
