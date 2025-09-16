"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { ChevronLeft, ChevronRight, Eye, Info } from "lucide-react"
import type { CSVData, FieldConfig, DelimiterType } from "@/app/page"

interface PreviewTableProps {
  csvData: CSVData
  fields: FieldConfig[]
  delimiter: DelimiterType
  onPreviewReady: () => void
}

export function PreviewTable({ csvData, fields, delimiter, onPreviewReady }: PreviewTableProps) {
  const [currentPage, setCurrentPage] = useState(0)
  const [processedData, setProcessedData] = useState<{ headers: string[]; rows: string[][] } | null>(null)

  const rowsPerPage = 10

  // Process data based on field configuration
  useEffect(() => {
    const selectedFields = fields.filter((field) => field.selected).sort((a, b) => a.order - b.order)

    if (selectedFields.length === 0) {
      setProcessedData(null)
      return
    }

    // Get column indices for selected fields
    const columnIndices = selectedFields
      .map((field) => csvData.headers.indexOf(field.name))
      .filter((index) => index !== -1)

    // Extract headers and data for selected columns
    const headers = selectedFields.map((field) => field.name)
    const rows = csvData.rows.map((row) => columnIndices.map((index) => row[index] || ""))

    // Apply formatting (simplified for preview)
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
            // Simple date formatting - in a real app, you'd use a proper date library
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

    setProcessedData({ headers, rows: formattedRows })
    onPreviewReady()
  }, [csvData, fields, onPreviewReady])

  if (!processedData) {
    return (
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>Selecione pelo menos um campo para visualizar a pré-visualização.</AlertDescription>
      </Alert>
    )
  }

  const totalPages = Math.ceil(processedData.rows.length / rowsPerPage)
  const startIndex = currentPage * rowsPerPage
  const endIndex = Math.min(startIndex + rowsPerPage, processedData.rows.length)
  const currentRows = processedData.rows.slice(startIndex, endIndex)

  const selectedFields = fields.filter((field) => field.selected)

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Eye className="w-4 h-4 text-primary" />
          <h3 className="font-medium">Pré-visualização dos Dados</h3>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="secondary">{processedData.rows.length} linhas</Badge>
          <Badge variant="secondary">{processedData.headers.length} colunas</Badge>
        </div>
      </div>

      {/* Table */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">
            Mostrando {startIndex + 1}-{endIndex} de {processedData.rows.length} registros
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  {processedData.headers.map((header, index) => {
                    const field = selectedFields.find((f) => f.name === header)
                    return (
                      <th key={index} className="text-left p-3 font-medium">
                        <div className="flex items-center space-x-2">
                          <span>{header}</span>
                          {field && (
                            <Badge variant="outline" className="text-xs">
                              {field.format}
                            </Badge>
                          )}
                        </div>
                      </th>
                    )
                  })}
                </tr>
              </thead>
              <tbody>
                {currentRows.map((row, rowIndex) => (
                  <tr key={startIndex + rowIndex} className="border-b hover:bg-muted/25">
                    {row.map((cell, cellIndex) => (
                      <td key={cellIndex} className="p-3">
                        <div className="max-w-[200px] truncate" title={cell}>
                          {cell || "-"}
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Página {currentPage + 1} de {totalPages}
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
              disabled={currentPage === 0}
            >
              <ChevronLeft className="w-4 h-4" />
              Anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(Math.min(totalPages - 1, currentPage + 1))}
              disabled={currentPage === totalPages - 1}
            >
              Próxima
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Summary */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          <strong>Resumo:</strong> {processedData.rows.length} registros serão exportados com{" "}
          {processedData.headers.length} campos selecionados. A formatação será aplicada durante a exportação.
        </AlertDescription>
      </Alert>
    </div>
  )
}
