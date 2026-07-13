# Access-driven WinForms offline runtime case

## Situation

A .NET 6 WinForms upper-computer application launched and compiled, but the detection sequence was largely unfinished and production devices were unavailable. The practical target was a complete offline demonstration, not speculative hardware integration.

## Effective structure

- `AccessRepository`: resolves `Setting.mdb` from `AppContext.BaseDirectory`; loads parts and joins part-specific settings to base test definitions; uses parameterized queries.
- Detection models: part, step, and execution-result records/classes.
- `IDetectionDevice`: narrow asynchronous step-execution boundary.
- Offline device: simulates PLC, scanner, delay, vision, Modbus, string checks, and screen changes; database scripts are logged but not executed.
- Detection engine: orders/runs steps, skips disabled items, reports progress, honors cancellation, and stops on failure.
- Runtime settings: explicit `OfflineSimulation=true`; malformed/missing configuration fails closed.
- UI: database-driven product selection, visible step results/logs, Start/Stop state management, and single-instance settings form.

## Access-specific details

- Wrap reserved or ambiguous names such as `[User]` and table/column identifiers in brackets.
- `OleDb` parameters are positional even when named in code; add them in SQL placeholder order.
- For per-part limits, treat both `NULL` and blank strings as absent before falling back to base settings.
- Copy the `.mdb` with `PreserveNewest`; copy safety configuration deliberately so deployed behavior is predictable.

## Verification sequence from WSL

1. Run `powershell.exe` and build the Windows project natively.
2. Launch the produced `.exe` with `Start-Process -PassThru`.
3. Refresh the process object and inspect `Responding` and `MainWindowTitle`.
4. Stop the process before cleaning/restoring outputs because .NET and OleDb assemblies may remain locked.
5. Restore tracked `bin/obj` files if the legacy repository includes them, run `git diff --check` on source, then commit.

## Review lessons

A coding-agent review caught durable edge cases: custom repository connection strings should not still require the default database file; blank overrides need fallback handling; cancellation and disposed-form logging need care; and settings windows should be reused rather than multiplied. Independently rerun builds after agent work, especially when the agent times out after editing.
