"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Download, FileText, CheckCircle, Loader2 } from "lucide-react"
import type { CSVData, FieldConfig, DelimiterType } from "@/app/page"

interface ExportControlsProps {
  csvData: CSVData
  fields: FieldConfig[]
  delimiter: DelimiterType
}

export function ExportControls({ csvData, fields, delimiter }: ExportControlsProps) {
  const [exportFormat, setExportFormat] = useState<"csv" | "tsv" | "txt">("csv")
  const [outputDelimiter, setOutputDelimiter] = useState<DelimiterType>(delimiter)
  const [isExporting, setIsExporting] = useState(false)
  const [exportComplete, setExportComplete] = useState(false)

  const selectedFields = fields.filter((field) => field.selected).sort((a, b) => a.order - b.order)

  const formatData = () => {
    // Get column indices for selected fields
    const columnIndices = selectedFields
      .map((field) => csvData.headers.indexOf(field.name))
      .filter((index) => index !== -1)

    // Extract headers and data for selected columns
    const headers = selectedFields.map((field) => field.name)
    const rows = csvData.rows.map((row) => columnIndices.map((index) => row[index] || ""))

    // Apply formatting
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
            // Simple date formatting
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

    try {
      // Simulate processing time
      await new Promise((resolve) => setTimeout(resolve, 1000))

      const formattedData = formatData()
      const csvContent = generateCSV(formattedData, outputDelimiter)

      // Create and download file
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
      const link = document.createElement("a")
      const url = URL.createObjectURL(blob)

      link.setAttribute("href", url)
      link.setAttribute("download", `dados_processados.${exportFormat}`)
      link.style.visibility = "hidden"
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      setExportComplete(true)
    } catch (error) {
      console.error("Erro ao exportar:", error)
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

  return (
    <div className="space-y-6">
      {/* Export Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Configurações de Exportação</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Format Selection */}
            <div className="space-y-2">
              <Label htmlFor="export-format">Formato do arquivo</Label>
              <Select value={exportFormat} onValueChange={(value) => setExportFormat(value as any)}>
                <SelectTrigger id="export-format">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="csv">CSV (Comma Separated Values)</SelectItem>
                  <SelectItem value="tsv">TSV (Tab Separated Values)</SelectItem>
                  <SelectItem value="txt">TXT (Texto simples)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Delimiter Selection */}
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
          </div>
        </CardContent>
      </Card>

      {/* Export Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center space-x-2">
            <FileText className="w-4 h-4" />
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
              <div className="text-2xl font-bold text-primary">{getDelimiterLabel(outputDelimiter).split(" ")[0]}</div>
              <div className="text-sm text-muted-foreground">Delimitador</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Selected Fields */}
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

      {/* Export Button */}
      <div className="flex flex-col items-center space-y-4">
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
              Baixar Arquivo Processado
            </>
          )}
        </Button>

        {exportComplete && (
          <Alert className="max-w-md">
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Sucesso!</strong> Seu arquivo foi processado e baixado com sucesso.
            </AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  )
}
