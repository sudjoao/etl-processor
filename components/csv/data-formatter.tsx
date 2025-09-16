"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Type, Hash, Calendar, DollarSign, Info } from "lucide-react"
import type { FieldConfig } from "@/app/page"

interface DataFormatterProps {
  fields: FieldConfig[]
  onFieldsChange: (fields: FieldConfig[]) => void
}

interface FormatOption {
  value: FieldConfig["format"]
  label: string
  description: string
  icon: React.ReactNode
  example: string
  options?: {
    dateFormat?: string
    currencySymbol?: string
    decimalPlaces?: number
  }
}

export function DataFormatter({ fields, onFieldsChange }: DataFormatterProps) {
  const [localFields, setLocalFields] = useState<FieldConfig[]>(fields)

  const formatOptions: FormatOption[] = [
    {
      value: "text",
      label: "Texto",
      description: "Mantém como texto simples",
      icon: <Type className="w-4 h-4" />,
      example: "João Silva",
    },
    {
      value: "number",
      label: "Número",
      description: "Formata como número",
      icon: <Hash className="w-4 h-4" />,
      example: "1,234.56",
    },
    {
      value: "date",
      label: "Data",
      description: "Formata como data",
      icon: <Calendar className="w-4 h-4" />,
      example: "01/12/2024",
      options: {
        dateFormat: "DD/MM/YYYY",
      },
    },
    {
      value: "currency",
      label: "Moeda",
      description: "Formata como valor monetário",
      icon: <DollarSign className="w-4 h-4" />,
      example: "R$ 1.234,56",
      options: {
        currencySymbol: "R$",
        decimalPlaces: 2,
      },
    },
  ]

  const handleFormatChange = (fieldName: string, format: FieldConfig["format"]) => {
    setLocalFields((prev) => prev.map((field) => (field.name === fieldName ? { ...field, format } : field)))
  }

  const handleConfirm = () => {
    onFieldsChange(localFields)
  }

  const selectedFields = localFields.filter((field) => field.selected)

  const getFormatIcon = (format: FieldConfig["format"]) => {
    const option = formatOptions.find((opt) => opt.value === format)
    return option?.icon || <Type className="w-4 h-4" />
  }

  const getFormatExample = (format: FieldConfig["format"]) => {
    const option = formatOptions.find((opt) => opt.value === format)
    return option?.example || "Exemplo"
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-medium">Formatação de Dados</h3>
          <p className="text-sm text-muted-foreground">Configure o formato de cada campo selecionado</p>
        </div>
        <Badge variant="secondary">{selectedFields.length} campos para formatar</Badge>
      </div>

      {/* Format Options Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {formatOptions.map((option) => (
          <Card key={option.value} className="p-4">
            <div className="flex items-center space-x-2 mb-2">
              {option.icon}
              <h4 className="font-medium text-sm">{option.label}</h4>
            </div>
            <p className="text-xs text-muted-foreground mb-2">{option.description}</p>
            <code className="text-xs bg-muted px-2 py-1 rounded block">{option.example}</code>
          </Card>
        ))}
      </div>

      {/* Field Configuration */}
      <div className="space-y-4">
        {selectedFields.map((field) => (
          <Card key={field.name}>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center space-x-2">
                {getFormatIcon(field.format)}
                <span>{field.name}</span>
                <Badge variant="outline" className="text-xs">
                  Posição {field.order + 1}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Format Selection */}
                <div className="space-y-2">
                  <Label htmlFor={`format-${field.name}`}>Formato</Label>
                  <Select value={field.format} onValueChange={(value) => handleFormatChange(field.name, value as any)}>
                    <SelectTrigger id={`format-${field.name}`}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {formatOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          <div className="flex items-center space-x-2">
                            {option.icon}
                            <span>{option.label}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Preview */}
                <div className="space-y-2">
                  <Label>Exemplo de saída</Label>
                  <div className="p-3 bg-muted rounded-md">
                    <code className="text-sm">{getFormatExample(field.format)}</code>
                  </div>
                </div>
              </div>

              {/* Format-specific options */}
              {field.format === "date" && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t">
                  <div className="space-y-2">
                    <Label htmlFor={`date-format-${field.name}`}>Formato de data</Label>
                    <Select defaultValue="DD/MM/YYYY">
                      <SelectTrigger id={`date-format-${field.name}`}>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                        <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                        <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                        <SelectItem value="DD-MM-YYYY">DD-MM-YYYY</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}

              {field.format === "currency" && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 border-t">
                  <div className="space-y-2">
                    <Label htmlFor={`currency-symbol-${field.name}`}>Símbolo</Label>
                    <Select defaultValue="R$">
                      <SelectTrigger id={`currency-symbol-${field.name}`}>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="R$">R$ (Real)</SelectItem>
                        <SelectItem value="$">$ (Dólar)</SelectItem>
                        <SelectItem value="€">€ (Euro)</SelectItem>
                        <SelectItem value="£">£ (Libra)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor={`decimal-places-${field.name}`}>Casas decimais</Label>
                    <Input
                      id={`decimal-places-${field.name}`}
                      type="number"
                      min="0"
                      max="4"
                      defaultValue="2"
                      className="w-full"
                    />
                  </div>
                </div>
              )}

              {field.format === "number" && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t">
                  <div className="space-y-2">
                    <Label htmlFor={`decimal-places-${field.name}`}>Casas decimais</Label>
                    <Input
                      id={`decimal-places-${field.name}`}
                      type="number"
                      min="0"
                      max="10"
                      defaultValue="2"
                      className="w-full"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor={`thousand-separator-${field.name}`}>Separador de milhares</Label>
                    <Select defaultValue="comma">
                      <SelectTrigger id={`thousand-separator-${field.name}`}>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="comma">Vírgula (,)</SelectItem>
                        <SelectItem value="dot">Ponto (.)</SelectItem>
                        <SelectItem value="space">Espaço ( )</SelectItem>
                        <SelectItem value="none">Nenhum</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Info Alert */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          <strong>Dica:</strong> As configurações de formatação serão aplicadas aos dados durante a exportação. Você
          pode visualizar o resultado na próxima etapa.
        </AlertDescription>
      </Alert>

      {/* Confirm Button */}
      <div className="flex justify-end">
        <Button onClick={handleConfirm}>Aplicar Formatação</Button>
      </div>
    </div>
  )
}
