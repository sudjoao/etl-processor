"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Download, FileText, CheckCircle, Loader2, Database, BarChart3 } from "lucide-react"
import type { CSVData, FieldConfig, DelimiterType } from "@/app/page"
import { ApiService } from "@/lib/api"
import { DataWarehouseViewer } from "@/components/dw/data-warehouse-viewer"

interface ExportControlsProps {
  csvData: CSVData
  fields: FieldConfig[]
  delimiter: DelimiterType
}

type SQLDatabaseType = "ansi" | "mysql" | "postgresql" | "sqlite" | "sqlserver"
type ExportFormatType = "csv" | "tsv" | "txt" | "sql"

export function ExportControls({ csvData, fields, delimiter }: ExportControlsProps) {
  const [exportFormat, setExportFormat] = useState<ExportFormatType>("csv")
  const [outputDelimiter, setOutputDelimiter] = useState<DelimiterType>(delimiter)
  const [isExporting, setIsExporting] = useState(false)
  const [exportComplete, setExportComplete] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)
  const [sqlDatabaseType, setSqlDatabaseType] = useState<SQLDatabaseType>("ansi")
  const [createTable, setCreateTable] = useState(true)
  const [tableName, setTableName] = useState("dados_importados")
  const [showDwViewer, setShowDwViewer] = useState(false)
  const [generatedSql, setGeneratedSql] = useState<string | null>(null)

  const selectedFields = fields.filter((field) => field.selected).sort((a, b) => a.order - b.order)

  const formatData = () => {
    const columnIndices = selectedFields
      .map((field) => csvData.headers.indexOf(field.name))
      .filter((index) => index !== -1)

    const headers = selectedFields.map((field) => field.name)
    const rows = csvData.rows.map((row) => columnIndices.map((index) => row[index] || ""))

    const formattedRows = rows.map((row) =>
      row.map((cell, cellIndex) => {
        const field = selectedFields[cellIndex]
        if (!field) return cell

        switch (field.format) {
          case "number":
            const num = Number.parseFloat(cell)
            return isNaN(num) ? cell : num.toLocaleString("pt-BR", { minimumFractionDigits: 2 })
          case "currency":
            const curr = Number.parseFloat(cell)
            return isNaN(curr) ? cell : curr.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })
          case "date":
            if (cell.match(/^\d{4}-\d{2}-\d{2}$/)) {
              const [year, month, day] = cell.split("-")
              return `${day}/${month}/${year}`
            }
            return cell
          default:
            return cell
        }
      }),
    )

    return { headers, rows: formattedRows }
  }

  const generateSQL = (data: { headers: string[]; rows: string[][] }) => {
    const sanitizeIdentifier = (name: string) => {
      return name.replace(/[^a-zA-Z0-9_]/g, "_").toLowerCase()
    }

    const getSQLType = (field: FieldConfig) => {
      switch (sqlDatabaseType) {
        case "mysql":
          switch (field.format) {
            case "number":
              return "DECIMAL(10,2)"
            case "currency":
              return "DECIMAL(10,2)"
            case "date":
              return "DATE"
            default:
              return "VARCHAR(255)"
          }
        case "postgresql":
          switch (field.format) {
            case "number":
              return "NUMERIC(10,2)"
            case "currency":
              return "NUMERIC(10,2)"
            case "date":
              return "DATE"
            default:
              return "VARCHAR(255)"
          }
        case "sqlite":
          switch (field.format) {
            case "number":
              return "REAL"
            case "currency":
              return "REAL"
            case "date":
              return "TEXT"
            default:
              return "TEXT"
          }
        case "sqlserver":
          switch (field.format) {
            case "number":
              return "DECIMAL(10,2)"
            case "currency":
              return "MONEY"
            case "date":
              return "DATE"
            default:
              return "NVARCHAR(255)"
          }
        default: // ANSI
          switch (field.format) {
            case "number":
              return "DECIMAL(10,2)"
            case "currency":
              return "DECIMAL(10,2)"
            case "date":
              return "DATE"
            default:
              return "VARCHAR(255)"
          }
      }
    }

    const escapeValue = (value: string, field: FieldConfig) => {
      if (value === "" || value === null || value === undefined) {
        return "NULL"
      }

      if (field.format === "number" || field.format === "currency") {
        const num = Number.parseFloat(value.replace(/[^\d.-]/g, ""))
        return isNaN(num) ? "NULL" : num.toString()
      }

      return `'${value.replace(/'/g, "''")}'`
    }

    let sql = ""

    if (createTable) {
      const sanitizedTableName = sanitizeIdentifier(tableName)
      sql += `-- Criação da tabela\n`

      if (sqlDatabaseType === "mysql") {
        sql += `DROP TABLE IF EXISTS \`${sanitizedTableName}\`;\n`
        sql += `CREATE TABLE \`${sanitizedTableName}\` (\n`
      } else if (sqlDatabaseType === "postgresql") {
        sql += `DROP TABLE IF EXISTS "${sanitizedTableName}" CASCADE;\n`
        sql += `CREATE TABLE "${sanitizedTableName}" (\n`
      } else {
        sql += `DROP TABLE IF EXISTS ${sanitizedTableName};\n`
        sql += `CREATE TABLE ${sanitizedTableName} (\n`
      }

      const columns = selectedFields.map((field, index) => {
        const columnName = sanitizeIdentifier(field.name)
        const sqlType = getSQLType(field)
        const isLast = index === selectedFields.length - 1

        if (sqlDatabaseType === "mysql") {
          return `  \`${columnName}\` ${sqlType}${isLast ? "" : ","}`
        } else if (sqlDatabaseType === "postgresql") {
          return `  "${columnName}" ${sqlType}${isLast ? "" : ","}`
        } else {
          return `  ${columnName} ${sqlType}${isLast ? "" : ","}`
        }
      })

      sql += columns.join("\n") + "\n"
      sql += ");\n\n"
    }

    sql += `-- Inserção dos dados\n`

    const sanitizedTableName = sanitizeIdentifier(tableName)
    const columnNames = selectedFields
      .map((field) => {
        const columnName = sanitizeIdentifier(field.name)
        if (sqlDatabaseType === "mysql") {
          return `\`${columnName}\``
        } else if (sqlDatabaseType === "postgresql") {
          return `"${columnName}"`
        } else {
          return columnName
        }
      })
      .join(", ")

    data.rows.forEach((row) => {
      const values = row.map((cell, index) => escapeValue(cell, selectedFields[index])).join(", ")

      if (sqlDatabaseType === "mysql") {
        sql += `INSERT INTO \`${sanitizedTableName}\` (${columnNames}) VALUES (${values});\n`
      } else if (sqlDatabaseType === "postgresql") {
        sql += `INSERT INTO "${sanitizedTableName}" (${columnNames}) VALUES (${values});\n`
      } else {
        sql += `INSERT INTO ${sanitizedTableName} (${columnNames}) VALUES (${values});\n`
      }
    })

    return sql
  }

  const generateCSV = (data: { headers: string[]; rows: string[][] }, delimiter: DelimiterType) => {
    const escapeField = (field: string) => {
      if (field.includes(delimiter) || field.includes('"') || field.includes("\n")) {
        return `"${field.replace(/"/g, '""')}"`
      }
      return field
    }

    const headerRow = data.headers.map(escapeField).join(delimiter)
    const dataRows = data.rows.map((row) => row.map(escapeField).join(delimiter))

    return [headerRow, ...dataRows].join("\n")
  }

  const handleExport = async () => {
    setIsExporting(true)
    setExportComplete(false)
    setExportError(null)

    try {
      let content: string
      let filename: string
      let mimeType: string

      if (exportFormat === "sql") {
        // Use API to generate SQL
        const csvContent = ApiService.csvDataToString(csvData, delimiter)

        const response = await ApiService.transformCsvToSql({
          csvContent,
          fields,
          tableName,
          delimiter,
          databaseType: sqlDatabaseType,
          includeCreateTable: createTable
        })

        if (!response.success) {
          throw new Error(response.error || "Erro ao gerar SQL")
        }

        content = response.sql
        setGeneratedSql(response.sql) // Save SQL for DW viewer
        filename = `${tableName}.sql`
        mimeType = "text/sql;charset=utf-8;"
      } else {
        // Generate CSV/TSV/TXT locally
        const formattedData = formatData()
        content = generateCSV(formattedData, outputDelimiter)
        filename = `dados_processados.${exportFormat}`
        mimeType = "text/csv;charset=utf-8;"
      }

      const blob = new Blob([content], { type: mimeType })
      const link = document.createElement("a")
      const url = URL.createObjectURL(blob)

      link.setAttribute("href", url)
      link.setAttribute("download", filename)
      link.style.visibility = "hidden"
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      setExportComplete(true)
    } catch (error) {
      console.error("Erro ao exportar:", error)
      const errorMessage = error instanceof Error ? error.message : 'Erro desconhecido'
      setExportError(errorMessage)
    } finally {
      setIsExporting(false)
    }
  }

  const getDelimiterLabel = (delimiter: DelimiterType) => {
    switch (delimiter) {
      case ",":
        return "Vírgula (,)"
      case ";":
        return "Ponto e vírgula (;)"
      case "\t":
        return "Tabulação"
      case "|":
        return "Pipe (|)"
      default:
        return delimiter
    }
  }

  const getSQLDatabaseLabel = (type: SQLDatabaseType) => {
    switch (type) {
      case "ansi":
        return "ANSI SQL (Padrão)"
      case "mysql":
        return "MySQL"
      case "postgresql":
        return "PostgreSQL"
      case "sqlite":
        return "SQLite"
      case "sqlserver":
        return "SQL Server"
      default:
        return type
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Configurações de Exportação</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="export-format">Formato do arquivo</Label>
              <Select value={exportFormat} onValueChange={(value) => setExportFormat(value as ExportFormatType)}>
                <SelectTrigger id="export-format">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="csv">CSV (Comma Separated Values)</SelectItem>
                  <SelectItem value="tsv">TSV (Tab Separated Values)</SelectItem>
                  <SelectItem value="txt">TXT (Texto simples)</SelectItem>
                  <SelectItem value="sql">SQL (Structured Query Language)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {exportFormat !== "sql" && (
              <div className="space-y-2">
                <Label htmlFor="output-delimiter">Delimitador de saída</Label>
                <Select value={outputDelimiter} onValueChange={(value) => setOutputDelimiter(value as DelimiterType)}>
                  <SelectTrigger id="output-delimiter">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value=",">{getDelimiterLabel(",")}</SelectItem>
                    <SelectItem value=";">{getDelimiterLabel(";")}</SelectItem>
                    <SelectItem value="\t">{getDelimiterLabel("\t")}</SelectItem>
                    <SelectItem value="|">{getDelimiterLabel("|")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            {exportFormat === "sql" && (
              <div className="space-y-2">
                <Label htmlFor="sql-database">Formato do banco de dados</Label>
                <Select value={sqlDatabaseType} onValueChange={(value) => setSqlDatabaseType(value as SQLDatabaseType)}>
                  <SelectTrigger id="sql-database">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ansi">{getSQLDatabaseLabel("ansi")}</SelectItem>
                    <SelectItem value="mysql">{getSQLDatabaseLabel("mysql")}</SelectItem>
                    <SelectItem value="postgresql">{getSQLDatabaseLabel("postgresql")}</SelectItem>
                    <SelectItem value="sqlite">{getSQLDatabaseLabel("sqlite")}</SelectItem>
                    <SelectItem value="sqlserver">{getSQLDatabaseLabel("sqlserver")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {exportFormat === "sql" && (
            <div className="space-y-4 pt-4 border-t">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="create-table"
                  checked={createTable}
                  onCheckedChange={(checked) => setCreateTable(checked as boolean)}
                />
                <Label htmlFor="create-table">Incluir comando CREATE TABLE</Label>
              </div>

              <div className="space-y-2">
                <Label htmlFor="table-name">Nome da tabela</Label>
                <Input
                  id="table-name"
                  value={tableName}
                  onChange={(e) => setTableName(e.target.value)}
                  placeholder="nome_da_tabela"
                />
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center space-x-2">
            {exportFormat === "sql" ? <Database className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
            <span>Resumo da Exportação</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">{csvData.rows.length}</div>
              <div className="text-sm text-muted-foreground">Registros</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">{selectedFields.length}</div>
              <div className="text-sm text-muted-foreground">Campos</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary">{exportFormat.toUpperCase()}</div>
              <div className="text-sm text-muted-foreground">Formato</div>
            </div>
            <div className="text-center">
              {exportFormat === "sql" ? (
                <>
                  <div className="text-2xl font-bold text-primary">
                    {getSQLDatabaseLabel(sqlDatabaseType).split(" ")[0]}
                  </div>
                  <div className="text-sm text-muted-foreground">Banco</div>
                </>
              ) : (
                <>
                  <div className="text-2xl font-bold text-primary">
                    {getDelimiterLabel(outputDelimiter).split(" ")[0]}
                  </div>
                  <div className="text-sm text-muted-foreground">Delimitador</div>
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Campos Selecionados</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {selectedFields.map((field, index) => (
              <Badge key={field.name} variant="secondary" className="flex items-center space-x-1">
                <span>{index + 1}.</span>
                <span>{field.name}</span>
                <span className="text-xs">({field.format})</span>
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="flex flex-col items-center space-y-4">
        <div className="flex flex-col md:flex-row gap-4 w-full md:w-auto">
          <Button
            onClick={handleExport}
            disabled={isExporting || selectedFields.length === 0}
            size="lg"
            className="w-full md:w-auto"
          >
            {isExporting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Processando...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                {exportFormat === "sql" ? "Baixar Script SQL" : "Baixar Arquivo Processado"}
              </>
            )}
          </Button>

          {exportFormat === "sql" && generatedSql && (
            <Button
              onClick={() => setShowDwViewer(true)}
              variant="outline"
              size="lg"
              className="w-full md:w-auto"
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              Modelagem DW
            </Button>
          )}
        </div>

        {exportComplete && (
          <Alert className="max-w-md">
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Sucesso!</strong> Seu arquivo foi processado e baixado com sucesso.
            </AlertDescription>
          </Alert>
        )}

        {exportError && (
          <Alert variant="destructive" className="max-w-md">
            <AlertDescription>
              <strong>Erro!</strong> {exportError}
            </AlertDescription>
          </Alert>
        )}
      </div>

      {showDwViewer && generatedSql && (
        <div className="mt-8">
          <DataWarehouseViewer
            sqlContent={generatedSql}
            onClose={() => setShowDwViewer(false)}
          />
        </div>
      )}
    </div>
  )
}
