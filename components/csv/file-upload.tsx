"use client"

import { useState, useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { Upload, FileText, AlertCircle, CheckCircle } from "lucide-react"
import type { CSVData } from "@/app/page"

interface FileUploadProps {
  onFileLoad: (data: CSVData) => void
}

export function FileUpload({ onFileLoad }: FileUploadProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)

  const parseCSV = useCallback((content: string): CSVData => {
    const lines = content.split("\n").filter((line) => line.trim() !== "")
    if (lines.length === 0) {
      throw new Error("Arquivo CSV vazio")
    }

    // Assume comma as default delimiter for initial parsing
    // The actual delimiter will be configured in the next step
    const headers = lines[0].split(",").map((header) => header.trim().replace(/"/g, ""))
    const rows = lines.slice(1).map((line) => line.split(",").map((cell) => cell.trim().replace(/"/g, "")))

    return { headers, rows }
  }, [])

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0]
      if (!file) return

      setIsLoading(true)
      setError(null)
      setUploadProgress(0)
      setUploadedFile(file)

      try {
        // Simulate upload progress
        const progressInterval = setInterval(() => {
          setUploadProgress((prev) => {
            if (prev >= 90) {
              clearInterval(progressInterval)
              return 90
            }
            return prev + 10
          })
        }, 100)

        const content = await file.text()

        // Complete progress
        setUploadProgress(100)
        clearInterval(progressInterval)

        // Small delay for UX
        await new Promise((resolve) => setTimeout(resolve, 500))

        const csvData = parseCSV(content)

        if (csvData.headers.length === 0) {
          throw new Error("Nenhum cabeçalho encontrado no arquivo")
        }

        if (csvData.rows.length === 0) {
          throw new Error("Nenhum dado encontrado no arquivo")
        }

        onFileLoad(csvData)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao processar arquivo")
        setUploadProgress(0)
      } finally {
        setIsLoading(false)
      }
    },
    [onFileLoad, parseCSV],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "text/plain": [".txt"],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
    onDropRejected: (fileRejections) => {
      const rejection = fileRejections[0]
      if (rejection) {
        const error = rejection.errors[0]
        if (error?.code === "file-too-large") {
          setError("Arquivo muito grande. Tamanho máximo: 10MB")
        } else if (error?.code === "file-invalid-type") {
          setError("Tipo de arquivo inválido. Use apenas arquivos .csv ou .txt")
        } else {
          setError("Erro ao carregar arquivo")
        }
      }
    },
  })

  const resetUpload = () => {
    setUploadedFile(null)
    setError(null)
    setUploadProgress(0)
  }

  return (
    <div className="space-y-4">
      {!uploadedFile ? (
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragActive ? "border-primary bg-primary/5" : "border-border hover:border-primary/50 hover:bg-muted/50"}
          `}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center space-y-4">
            <div className={`p-4 rounded-full ${isDragActive ? "bg-primary/10" : "bg-muted"}`}>
              <Upload className={`w-8 h-8 ${isDragActive ? "text-primary" : "text-muted-foreground"}`} />
            </div>
            <div>
              <p className="text-lg font-medium">
                {isDragActive ? "Solte o arquivo aqui" : "Arraste seu arquivo CSV aqui"}
              </p>
              <p className="text-sm text-muted-foreground mt-1">ou clique para selecionar um arquivo</p>
            </div>
            <div className="text-xs text-muted-foreground">Formatos suportados: .csv, .txt • Tamanho máximo: 10MB</div>
          </div>
        </div>
      ) : (
        <div className="border rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-primary/10 rounded">
                <FileText className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="font-medium">{uploadedFile.name}</p>
                <p className="text-sm text-muted-foreground">{(uploadedFile.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {uploadProgress === 100 && !error && <CheckCircle className="w-5 h-5 text-green-500" />}
              <Button variant="outline" size="sm" onClick={resetUpload}>
                Trocar arquivo
              </Button>
            </div>
          </div>

          {isLoading && (
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span>Processando arquivo...</span>
                <span>{uploadProgress}%</span>
              </div>
              <Progress value={uploadProgress} className="h-2" />
            </div>
          )}
        </div>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!uploadedFile && (
        <div className="text-center">
          <Button variant="outline" onClick={() => document.querySelector('input[type="file"]')?.click()}>
            <Upload className="w-4 h-4 mr-2" />
            Selecionar Arquivo
          </Button>
        </div>
      )}
    </div>
  )
}
