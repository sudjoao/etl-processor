"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { FileUpload } from "@/components/csv/file-upload"
import { DelimiterConfig } from "@/components/csv/delimiter-config"
import { FieldSelector } from "@/components/csv/field-selector"
import { DataFormatter } from "@/components/csv/data-formatter"
import { PreviewTable } from "@/components/csv/preview-table"
import { ExportControls } from "@/components/csv/export-controls"
import { Upload, Settings, Filter, Palette, Eye, Download } from "lucide-react"

export type DelimiterType = "," | ";" | "\t" | "|"

export interface CSVData {
  headers: string[]
  rows: string[][]
}

export interface FieldConfig {
  name: string
  selected: boolean
  order: number
  format: "text" | "number" | "date" | "currency"
}

export default function CSVProcessor() {
  const [csvData, setCsvData] = useState<CSVData | null>(null)
  const [delimiter, setDelimiter] = useState<DelimiterType>(",")
  const [fields, setFields] = useState<FieldConfig[]>([])
  const [currentStep, setCurrentStep] = useState(1)

  const steps = [
    { id: 1, title: "Upload", icon: Upload, description: "Carregar arquivo CSV" },
    { id: 2, title: "Configurar", icon: Settings, description: "Definir delimitador" },
    { id: 3, title: "Selecionar", icon: Filter, description: "Escolher campos" },
    { id: 4, title: "Formatar", icon: Palette, description: "Formatar dados" },
    { id: 5, title: "Visualizar", icon: Eye, description: "Pré-visualizar" },
    { id: 6, title: "Exportar", icon: Download, description: "Baixar resultado" },
  ]

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-4 text-balance">Processador de CSV</h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            Ferramenta profissional para transformar e processar arquivos CSV com controle total sobre delimitadores,
            campos e formatação de dados.
          </p>
        </div>

        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex justify-center">
            <div className="flex items-center space-x-4 overflow-x-auto pb-4">
              {steps.map((step, index) => {
                const Icon = step.icon
                const isActive = currentStep === step.id
                const isCompleted = currentStep > step.id

                return (
                  <div key={step.id} className="flex items-center">
                    <div className="flex flex-col items-center min-w-0">
                      <div
                        className={`
                        w-12 h-12 rounded-full flex items-center justify-center border-2 transition-colors
                        ${
                          isActive
                            ? "bg-primary border-primary text-primary-foreground"
                            : isCompleted
                              ? "bg-accent border-accent text-accent-foreground"
                              : "bg-muted border-border text-muted-foreground"
                        }
                      `}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <div className="mt-2 text-center">
                        <div className={`text-sm font-medium ${isActive ? "text-primary" : "text-muted-foreground"}`}>
                          {step.title}
                        </div>
                        <div className="text-xs text-muted-foreground hidden sm:block">{step.description}</div>
                      </div>
                    </div>
                    {index < steps.length - 1 && (
                      <div className={`w-8 h-0.5 mx-4 ${isCompleted ? "bg-accent" : "bg-border"}`} />
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Controls */}
          <div className="lg:col-span-2 space-y-6">
            {/* Step 1: File Upload */}
            <Card className={currentStep === 1 ? "ring-2 ring-primary" : ""}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="w-5 h-5" />
                  Upload do Arquivo CSV
                </CardTitle>
                <CardDescription>Selecione ou arraste seu arquivo CSV para começar o processamento</CardDescription>
              </CardHeader>
              <CardContent>
                <FileUpload
                  onFileLoad={(data) => {
                    setCsvData(data)
                    setCurrentStep(2)
                  }}
                />
              </CardContent>
            </Card>

            {/* Step 2: Delimiter Configuration */}
            {csvData && (
              <Card className={currentStep === 2 ? "ring-2 ring-primary" : ""}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="w-5 h-5" />
                    Configuração do Delimitador
                  </CardTitle>
                  <CardDescription>Escolha o delimitador usado no seu arquivo CSV</CardDescription>
                </CardHeader>
                <CardContent>
                  <DelimiterConfig
                    delimiter={delimiter}
                    onDelimiterChange={(newDelimiter) => {
                      setDelimiter(newDelimiter)
                      setCurrentStep(3)
                    }}
                    csvData={csvData}
                  />
                </CardContent>
              </Card>
            )}

            {/* Step 3: Field Selection */}
            {csvData && currentStep >= 3 && (
              <Card className={currentStep === 3 ? "ring-2 ring-primary" : ""}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Filter className="w-5 h-5" />
                    Seleção de Campos
                  </CardTitle>
                  <CardDescription>Escolha quais campos incluir e defina a ordem</CardDescription>
                </CardHeader>
                <CardContent>
                  <FieldSelector
                    headers={csvData.headers}
                    fields={fields}
                    onFieldsChange={(newFields) => {
                      setFields(newFields)
                      setCurrentStep(4)
                    }}
                  />
                </CardContent>
              </Card>
            )}

            {/* Step 4: Data Formatting */}
            {fields.length > 0 && currentStep >= 4 && (
              <Card className={currentStep === 4 ? "ring-2 ring-primary" : ""}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Palette className="w-5 h-5" />
                    Formatação de Dados
                  </CardTitle>
                  <CardDescription>Configure o formato de cada campo selecionado</CardDescription>
                </CardHeader>
                <CardContent>
                  <DataFormatter
                    fields={fields}
                    onFieldsChange={(newFields) => {
                      setFields(newFields)
                      setCurrentStep(5)
                    }}
                  />
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right Column - Preview and Export */}
          <div className="space-y-6">
            {/* Step 5: Preview */}
            {csvData && fields.some((f) => f.selected) && currentStep >= 5 && (
              <Card className={currentStep === 5 ? "ring-2 ring-primary" : ""}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Eye className="w-5 h-5" />
                    Pré-visualização
                  </CardTitle>
                  <CardDescription>Visualize como ficará o arquivo final</CardDescription>
                </CardHeader>
                <CardContent>
                  <PreviewTable
                    csvData={csvData}
                    fields={fields}
                    delimiter={delimiter}
                    onPreviewReady={() => setCurrentStep(6)}
                  />
                </CardContent>
              </Card>
            )}

            {/* Step 6: Export */}
            {currentStep >= 6 && csvData && fields.some((f) => f.selected) && (
              <Card className="ring-2 ring-accent">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Download className="w-5 h-5" />
                    Exportar Resultado
                  </CardTitle>
                  <CardDescription>Baixe o arquivo CSV processado</CardDescription>
                </CardHeader>
                <CardContent>
                  <ExportControls csvData={csvData} fields={fields} delimiter={delimiter} />
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
