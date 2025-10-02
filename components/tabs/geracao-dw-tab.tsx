"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { FileUpload } from "@/components/csv/file-upload"
import { DelimiterConfig } from "@/components/csv/delimiter-config"
import { FieldSelector } from "@/components/csv/field-selector"
import { DataFormatter } from "@/components/csv/data-formatter"
import { PreviewTable } from "@/components/csv/preview-table"
import { ExportControls } from "@/components/csv/export-controls"
import { Upload, Settings, Filter, Palette, Eye, Download, ChevronLeft, ChevronRight } from "lucide-react"

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

export default function GeracaoDwTab() {
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

  const goToStep = (stepId: number) => {
    setCurrentStep(stepId)
  }

  const goToPreviousStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const goToNextStep = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1)
    }
  }

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <Card className="ring-2 ring-primary">
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
                  goToNextStep()
                }}
              />
            </CardContent>
          </Card>
        )

      case 2:
        return csvData ? (
          <Card className="ring-2 ring-primary">
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
                  goToNextStep()
                }}
                csvData={csvData}
              />
            </CardContent>
          </Card>
        ) : null

      case 3:
        return csvData ? (
          <Card className="ring-2 ring-primary">
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
                  goToNextStep()
                }}
              />
            </CardContent>
          </Card>
        ) : null

      case 4:
        return fields.length > 0 ? (
          <Card className="ring-2 ring-primary">
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
                  goToNextStep()
                }}
              />
            </CardContent>
          </Card>
        ) : null

      case 5:
        return csvData && fields.some((f) => f.selected) ? (
          <Card className="ring-2 ring-primary">
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
                onPreviewReady={() => goToNextStep()}
              />
            </CardContent>
          </Card>
        ) : null

      case 6:
        return csvData && fields.some((f) => f.selected) ? (
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
        ) : null

      default:
        return null
    }
  }

  return (
    <div className="space-y-6">
      {/* Progress Steps */}
      <div className="flex justify-center">
        <div className="flex items-center space-x-4 overflow-x-auto pb-4">
          {steps.map((step, index) => {
            const Icon = step.icon
            const isActive = currentStep === step.id
            const isCompleted = currentStep > step.id

            return (
              <div key={step.id} className="flex items-center">
                <div className="flex flex-col items-center min-w-0">
                  <button
                    onClick={() => {
                      if (step.id <= currentStep || isCompleted) {
                        goToStep(step.id)
                      }
                    }}
                    disabled={step.id > currentStep && !isCompleted}
                    className={`
                    w-12 h-12 rounded-full flex items-center justify-center border-2 transition-colors cursor-pointer hover:scale-105 disabled:cursor-not-allowed disabled:hover:scale-100
                    ${
                      isActive
                        ? "bg-primary border-primary text-primary-foreground"
                        : isCompleted
                          ? "bg-accent border-accent text-accent-foreground hover:bg-accent/80"
                          : "bg-muted border-border text-muted-foreground"
                    }
                  `}
                  >
                    <Icon className="w-5 h-5" />
                  </button>
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

      {/* Current Step Content */}
      <div className="min-h-[400px] flex items-start justify-center">{renderCurrentStep()}</div>

      {/* Navigation */}
      <div className="flex justify-between items-center">
        <Button
          variant="outline"
          onClick={goToPreviousStep}
          disabled={currentStep === 1}
          className="flex items-center gap-2 bg-transparent"
        >
          <ChevronLeft className="w-4 h-4" />
          Anterior
        </Button>

        <div className="text-sm text-muted-foreground">
          Passo {currentStep} de {steps.length}
        </div>

        <Button
          variant="outline"
          onClick={goToNextStep}
          disabled={currentStep === steps.length}
          className="flex items-center gap-2 bg-transparent"
        >
          Próximo
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}
