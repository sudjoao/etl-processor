"use client"

import { useState, useCallback, useEffect } from "react"
import { useDropzone } from "react-dropzone"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { 
  Upload, 
  FileText, 
  AlertCircle, 
  CheckCircle, 
  Loader2, 
  Database, 
  Clock, 
  Trash2,
  Info
} from "lucide-react"
import { ApiService } from "@/lib/api"
import NLQChat from "@/components/nlq-chat"

interface SessionInfo {
  session_id: string
  schema_name: string
  created_at: string
  expires_at: string
  status: string
  provisioned_at?: string
  time_remaining_seconds: number
}

export default function ConfiguracaoExploracaoTab() {
  const [sqlFile, setSqlFile] = useState<File | null>(null)
  const [sqlContent, setSqlContent] = useState<string>("")
  const [isUploading, setIsUploading] = useState(false)
  const [isProvisioning, setIsProvisioning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null)
  const [timeRemaining, setTimeRemaining] = useState<number>(0)

  // Update countdown timer
  useEffect(() => {
    if (sessionInfo && sessionInfo.time_remaining_seconds > 0) {
      const timer = setInterval(() => {
        setTimeRemaining(prev => {
          const newTime = Math.max(0, prev - 1)
          if (newTime === 0) {
            // Session expired, refresh session info
            refreshSessionInfo()
          }
          return newTime
        })
      }, 1000)

      setTimeRemaining(sessionInfo.time_remaining_seconds)
      return () => clearInterval(timer)
    }
  }, [sessionInfo])

  const refreshSessionInfo = async () => {
    if (!sessionInfo) return
    
    try {
      const response = await ApiService.getNlqSessionInfo(sessionInfo.session_id)
      if (response.success) {
        setSessionInfo(response.session)
      }
    } catch (err) {
      console.error("Failed to refresh session info:", err)
    }
  }

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setIsUploading(true)
    setError(null)
    setSuccess(null)

    try {
      const content = await file.text()
      
      // Basic SQL validation
      if (!content.trim()) {
        throw new Error("O arquivo SQL está vazio")
      }

      if (!content.toLowerCase().includes('create')) {
        throw new Error("O arquivo deve conter comandos DDL (CREATE TABLE, etc.)")
      }

      setSqlFile(file)
      setSqlContent(content)
      setSuccess("Arquivo SQL carregado com sucesso!")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar arquivo SQL")
    } finally {
      setIsUploading(false)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/sql": [".sql"],
      "text/plain": [".sql", ".txt"],
    },
    maxFiles: 1,
    maxSize: 5 * 1024 * 1024, // 5MB
    onDropRejected: (fileRejections) => {
      const rejection = fileRejections[0]
      if (rejection) {
        const error = rejection.errors[0]
        if (error?.code === "file-too-large") {
          setError("Arquivo muito grande. Tamanho máximo: 5MB")
        } else if (error?.code === "file-invalid-type") {
          setError("Tipo de arquivo inválido. Use apenas arquivos .sql")
        } else {
          setError("Erro ao carregar arquivo")
        }
      }
    },
  })

  const createAndProvisionSession = async () => {
    if (!sqlContent) {
      setError("Nenhum arquivo SQL carregado")
      return
    }

    setIsProvisioning(true)
    setError(null)
    setSuccess(null)

    try {
      // Step 1: Create session
      const createResponse = await ApiService.createNlqSession({
        description: `Session for ${sqlFile?.name || 'uploaded SQL'}`,
        uploaded_file: sqlFile?.name
      })

      if (!createResponse.success) {
        throw new Error(createResponse.error || "Falha ao criar sessão")
      }

      const sessionId = createResponse.session.session_id

      // Step 2: Provision session with SQL content
      const provisionResponse = await ApiService.provisionNlqSession(sessionId, sqlContent)

      if (!provisionResponse.success) {
        throw new Error(provisionResponse.error || "Falha ao provisionar sessão")
      }

      // Step 3: Get session info
      const infoResponse = await ApiService.getNlqSessionInfo(sessionId)

      if (infoResponse.success) {
        setSessionInfo(infoResponse.session)
        setSuccess("Ambiente de exploração configurado com sucesso!")
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao configurar ambiente")
    } finally {
      setIsProvisioning(false)
    }
  }

  const cleanupSession = async () => {
    if (!sessionInfo) return

    try {
      const response = await ApiService.cleanupNlqSession(sessionInfo.session_id)
      
      if (response.success) {
        setSessionInfo(null)
        setSqlFile(null)
        setSqlContent("")
        setSuccess("Sessão finalizada com sucesso!")
      } else {
        setError(response.error || "Erro ao finalizar sessão")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao finalizar sessão")
    }
  }

  const resetUpload = () => {
    setSqlFile(null)
    setSqlContent("")
    setError(null)
    setSuccess(null)
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Configuração de Exploração</h2>
        <p className="text-muted-foreground">
          Importe um arquivo SQL com schema DDL para criar um ambiente de exploração de dados
        </p>
      </div>

      {/* Session Status */}
      {sessionInfo && (
        <Card className="border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-800">
              <Database className="w-5 h-5" />
              Sessão Ativa
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-green-800">ID da Sessão:</p>
                <p className="text-sm text-green-600 font-mono">{sessionInfo.session_id}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-green-800">Schema:</p>
                <p className="text-sm text-green-600 font-mono">{sessionInfo.schema_name}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-green-800">Status:</p>
                <Badge variant={sessionInfo.status === 'provisioned' ? 'default' : 'secondary'}>
                  {sessionInfo.status}
                </Badge>
              </div>
              <div>
                <p className="text-sm font-medium text-green-800 flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  Tempo Restante:
                </p>
                <p className="text-sm text-green-600 font-mono">
                  {timeRemaining > 0 ? formatTime(timeRemaining) : "Expirado"}
                </p>
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button
                onClick={cleanupSession}
                variant="destructive"
                size="sm"
                className="flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Finalizar Sessão
              </Button>
              <Button
                onClick={refreshSessionInfo}
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                <Info className="w-4 h-4" />
                Atualizar Info
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* NLQ Chat Interface - Only show when session is provisioned */}
      {sessionInfo && sessionInfo.status === 'provisioned' && (
        <NLQChat
          sessionId={sessionInfo.session_id}
          schemaName={sessionInfo.schema_name}
        />
      )}

      {/* File Upload */}
      {!sessionInfo && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="w-5 h-5" />
              Upload do Arquivo SQL
            </CardTitle>
            <CardDescription>
              Selecione um arquivo SQL contendo comandos DDL (CREATE TABLE, etc.)
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!sqlFile ? (
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
                      {isDragActive ? "Solte o arquivo aqui" : "Arraste seu arquivo SQL aqui"}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      ou clique para selecionar (máximo 5MB)
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-primary" />
                    <div>
                      <p className="font-medium">{sqlFile.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {(sqlFile.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <Button onClick={resetUpload} variant="outline" size="sm">
                    Remover
                  </Button>
                </div>

                <Button
                  onClick={createAndProvisionSession}
                  disabled={isProvisioning}
                  className="w-full"
                  size="lg"
                >
                  {isProvisioning ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Configurando Ambiente...
                    </>
                  ) : (
                    <>
                      <Database className="w-4 h-4 mr-2" />
                      Configurar Ambiente de Exploração
                    </>
                  )}
                </Button>
              </div>
            )}

            {isUploading && (
              <div className="mt-4">
                <Progress value={50} className="w-full" />
                <p className="text-sm text-muted-foreground mt-2">Carregando arquivo...</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Error/Success Messages */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}
