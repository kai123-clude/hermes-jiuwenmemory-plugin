# Inspect Access MDB/ACCDB with PowerShell OleDb

Use this when analyzing Windows desktop/HMI apps from WSL and the project contains `.mdb`/`.accdb` configuration databases. It avoids needing Linux `mdbtools` or sudo if Windows has the Microsoft ACE/Jet OleDb provider installed.

## Minimal exporter

Create a temporary PowerShell script and run it with `powershell.exe` from WSL.

```powershell
param([string]$DbPath)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$connStr = "Provider=Microsoft.ACE.OLEDB.12.0;Data Source=$DbPath;Persist Security Info=False;"
$conn = New-Object System.Data.OleDb.OleDbConnection($connStr)
$conn.Open()
try {
  $schema = $conn.GetOleDbSchemaTable([System.Data.OleDb.OleDbSchemaGuid]::Tables, $null)
  $tables = @()
  foreach ($row in $schema.Rows) {
    $name = [string]$row['TABLE_NAME']
    $type = [string]$row['TABLE_TYPE']
    if ($type -eq 'TABLE' -and -not $name.StartsWith('MSys')) { $tables += $name }
  }
  Write-Output "TABLES: $($tables -join ', ')"

  foreach ($t in $tables) {
    Write-Output "`n=== TABLE $t ==="
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = "SELECT TOP 20 * FROM [$t]"
    $da = New-Object System.Data.OleDb.OleDbDataAdapter($cmd)
    $dt = New-Object System.Data.DataTable
    [void]$da.Fill($dt)
    $cols = [string[]]($dt.Columns | ForEach-Object { $_.ColumnName + ':' + $_.DataType.Name })
    Write-Output "ROWS_SAMPLE: $($dt.Rows.Count); COLUMNS: $($cols -join ', ')"
    if ($dt.Rows.Count -gt 0) { $dt | ConvertTo-Csv -NoTypeInformation | Select-Object -First 21 }
  }
} finally {
  $conn.Close()
}
```

Run from WSL:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass \
  -File "$(wslpath -w /tmp/export_mdb.ps1)" \
  -DbPath 'C:\path\to\Setting.mdb'
```

## Focused summaries

After discovering tables, run targeted queries for counts and distinct method/type columns. Example for HMI test databases:

```powershell
function Scalar($sql){ $cmd=$conn.CreateCommand(); $cmd.CommandText=$sql; return $cmd.ExecuteScalar() }
foreach($t in @('users','PartInfo','PartTestSetting','TestBaseInfo')) {
  try { Write-Output ("COUNT {0}: {1}" -f $t,(Scalar "SELECT COUNT(*) FROM [$t]")) } catch {}
}

$cmd=$conn.CreateCommand()
$cmd.CommandText='SELECT TestMethod, COUNT(*) AS Cnt FROM [TestBaseInfo] GROUP BY TestMethod ORDER BY COUNT(*) DESC'
$r=$cmd.ExecuteReader()
while($r.Read()){ Write-Output ("{0}: {1}" -f $r['TestMethod'],$r['Cnt']) }
$r.Close()
```

## What to extract for analysis

- Table names and row counts.
- User/auth table schema and whether passwords are plaintext.
- Product/model tables: model descriptions, part numbers, group IDs.
- Test/recipe tables: method names, PLC addresses, IP/port fields, thresholds, order indexes.
- Script/config fields: sample enough to identify dependencies and host APIs; do not flood the final answer with full script bodies.

## Pitfalls

- If output Chinese appears mojibake in the terminal, redirect to a file and read as UTF-8, or set `[Console]::OutputEncoding` as above. Some legacy `.mdb` strings may still depend on Windows code pages.
- ACE provider may be missing on some Windows hosts. In that case use installed Office/Access drivers, LibreOffice conversion, or `mdbtools` if available; capture the extraction method, not the transient missing-driver failure.
- Avoid leaking credentials unnecessarily in final output. It is okay to report “plaintext credentials exist” and exact schema; only include actual passwords if the user specifically needs audit/remediation detail.
