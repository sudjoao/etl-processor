"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Hash, MoreVertical, Info } from "lucide-react"
import type { DelimiterType, CSVData } from "@/app/page"

interface DelimiterConfigProps {
  delimiter: DelimiterType
  onDelimiterChange: (delimiter: DelimiterType) => void
  csvData: CSVData
}

interface DelimiterOption {
  value: DelimiterType
  label: string
  description: string
  icon: React.ReactNode
  example: string
}

export function DelimiterConfig({ delimiter, onDelimiterChange, csvData }: DelimiterConfigProps) {
  const [previewData, setPreviewData] = useState<{ headers: string[]; rows: string[][] } | null>(null)
  const [selectedDelimiter, setSelectedDelimiter] = useState<DelimiterType>(delimiter)

  const delimiterOptions: DelimiterOption[] = [
    {
      value: ",",
      label: "Vírgula",
      description: "Padrão mais comum",
      icon: <span className="font-mono text-sm">,</span>,
      example: "nome,idade,cidade",
    },
    {
      value: ";",
      label: "Ponto e vírgula",
      description: "Comum no Brasil",
      icon: <span className="font-mono text-sm">;</span>,
      example: "nome;idade;cidade",
    },
    {
      value: "\t",
      label: "Tabulação",
      description: "Separação por tabs",
      icon: <Hash className="w-4 h-4" />,
      example: "nome    idade    cidade",
    },
    {
      value: "|",
      label: "Pipe",
      description: "Separação vertical",
      icon: <MoreVertical className="w-4 h-4" />,
      example: "nome|idade|cidade",
    },
  ]

  // Parse CSV with selected delimiter
  const parseWithDelimiter = (delimiter: DelimiterType) => {
    try {
      // Get raw content by joining back the original data
      const rawContent = [csvData.headers.join(","), ...csvData.rows.map((row) => row.join(","))].join("\n")

      const lines = rawContent.split("\n").filter((line) => line.trim() !== "")
      if (lines.length === 0) return null

      const headers = lines[0]
        .split(delimiter)
        .map((header) => header.trim().replace(/^["']|["']$/g, ""))
        .filter((header) => header !== "")

      const rows = lines.slice(1).map(
        (line) =>
          line
            .split(delimiter)
            .map((cell) => cell.trim().replace(/^["']|["']$/g, ""))
            .slice(0, headers.length), // Ensure same number of columns
      )

      return { headers, rows: rows.slice(0, 5) } // Show only first 5 rows for preview
    } catch (error) {
      return null
    }
  }

  useEffect(() => {
    const preview = parseWithDelimiter(selectedDelimiter)
    setPreviewData(preview)
  }, [selectedDelimiter, csvData])

  const handleDelimiterSelect = (newDelimiter: DelimiterType) => {
    setSelectedDelimiter(newDelimiter)
  }

  const handleConfirm = () => {
    onDelimiterChange(selectedDelimiter)
  }

  const getDelimiterStats = (delimiter: DelimiterType) => {
    const preview = parseWithDelimiter(delimiter)
    if (!preview) return { columns: 0, valid: false }

    const columns = preview.headers.length
    const valid = columns > 1 && preview.headers.every((header) => header.trim() !== "")

    return { columns, valid }
  }

  return (
    <div className="space-y-6">
      {/* Delimiter Options */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {delimiterOptions.map((option) => {
          const stats = getDelimiterStats(option.value)
          const isSelected = selectedDelimiter === option.value

          return (
            <Card
              key={option.value}
              className={`cursor-pointer transition-all hover:shadow-md ${
                isSelected ? "ring-2 ring-primary bg-primary/5" : "hover:border-primary/50"
              }`}
              onClick={() => handleDelimiterSelect(option.value)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-muted rounded-md">{option.icon}</div>
                    <div>
                      <h3 className="font-medium">{option.label}</h3>
                      <p className="text-sm text-muted-foreground">{option.description}</p>
                    </div>
                  </div>
                  {isSelected && <Badge variant="default">Selecionado</Badge>}
                </div>

                <div className="space-y-2">
                  <div className="text-xs text-muted-foreground">Exemplo:</div>
                  <code className="text-xs bg-muted px-2 py-1 rounded block">{option.example}</code>

                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Colunas detectadas:</span>
                    <Badge variant={stats.valid ? "default" : "destructive"} className="text-xs">
                      {stats.columns}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Preview */}
      {previewData && (
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Info className="w-4 h-4 text-primary" />
            <h3 className="font-medium">Pré-visualização com delimitador selecionado</h3>
          </div>

          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      {previewData.headers.map((header, index) => (
                        <th key={index} className="text-left p-3 font-medium">
                          {header || `Coluna ${index + 1}`}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {previewData.rows.slice(0, 3).map((row, rowIndex) => (
                      <tr key={rowIndex} className="border-b">
                        {row.map((cell, cellIndex) => (
                          <td key={cellIndex} className="p-3">
                            {cell || "-"}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {previewData.headers.length <= 1 && (
            <Alert variant="destructive">
              <AlertDescription>
                O delimitador selecionado não parece estar correto. Apenas {previewData.headers.length} coluna foi
                detectada.
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}

      {/* Confirm Button */}
      <div className="flex justify-end">
        <Button onClick={handleConfirm} disabled={!previewData || previewData.headers.length <= 1}>
          Confirmar Delimitador
        </Button>
      </div>
    </div>
  )
}
