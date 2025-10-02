"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription } from "@/components/ui/alert"
import * as ScrollAreaPrimitive from "@radix-ui/react-scroll-area"
import { 
  Send, 
  Loader2, 
  MessageSquare, 
  Database,
  AlertCircle,
  CheckCircle,
  Code
} from "lucide-react"
import { ApiService } from "@/lib/api"

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sqlQuery?: string
  queryResult?: any
  error?: string
}

interface NLQChatProps {
  sessionId: string
  schemaName: string
}

export default function NLQChat({ sessionId, schemaName }: NLQChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  // Add welcome message on mount
  useEffect(() => {
    setMessages([{
      id: 'welcome',
      role: 'assistant',
      content: `Hello! I'm your AI database assistant. I have access to your schema **${schemaName}** and can help you explore your data.\n\nYou can ask me questions like:\n- "How many tables does my schema have?"\n- "Show me the first 5 records from dim_movie"\n- "What columns does the fact_dados_importados table have?"\n- "How many rows are in each table?"\n\nWhat would you like to know?`,
      timestamp: new Date().toISOString()
    }])
  }, [schemaName])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput("")
    setIsLoading(true)
    setError(null)

    try {
      // Build conversation history for context
      const conversationHistory = messages
        .filter(m => m.id !== 'welcome')
        .map(m => ({
          role: m.role,
          content: m.content
        }))

      const response = await ApiService.queryNlqSession(
        sessionId,
        userMessage.content,
        conversationHistory
      )

      if (response.success) {
        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: response.response,
          timestamp: response.timestamp,
          sqlQuery: response.sql_query,
          queryResult: response.query_result
        }

        setMessages(prev => [...prev, assistantMessage])
      } else {
        throw new Error(response.error || 'Failed to process query')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      setError(errorMessage)
      
      const errorAssistantMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `I encountered an error: ${errorMessage}`,
        timestamp: new Date().toISOString(),
        error: errorMessage
      }
      
      setMessages(prev => [...prev, errorAssistantMessage])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const formatQueryResult = (result: any) => {
    if (!result) return null

    if (!result.success) {
      return (
        <Alert variant="destructive" className="mt-2">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{result.error}</AlertDescription>
        </Alert>
      )
    }

    if (result.type === 'select' && result.rows) {
      return (
        <div className="mt-2 border rounded-lg overflow-hidden">
          <div className="bg-muted px-3 py-2 text-sm font-medium">
            Query Results ({result.row_count} rows)
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  {result.columns.map((col: string) => (
                    <th key={col} className="px-3 py-2 text-left font-medium">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.rows.slice(0, 100).map((row: any, idx: number) => (
                  <tr key={idx} className="border-t">
                    {result.columns.map((col: string) => (
                      <td key={col} className="px-3 py-2">
                        {row[col] !== null && row[col] !== undefined 
                          ? String(row[col]) 
                          : <span className="text-muted-foreground italic">null</span>
                        }
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {result.row_count > 100 && (
            <div className="bg-muted px-3 py-2 text-sm text-muted-foreground">
              Showing first 100 of {result.row_count} rows
            </div>
          )}
        </div>
      )
    }

    if (result.type === 'modification') {
      return (
        <Alert className="mt-2">
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            Query executed successfully. {result.rows_affected} row(s) affected.
          </AlertDescription>
        </Alert>
      )
    }

    return null
  }

  return (
    <Card className="w-full h-[70vh] flex flex-col">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          AI Database Assistant
        </CardTitle>
        <CardDescription>
          Ask questions about your data in natural language
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col gap-4 min-h-0 overflow-hidden">
        <div className="flex-1 min-h-0 overflow-hidden border rounded-lg">
          <ScrollAreaPrimitive.Root className="h-full w-full overflow-hidden">
            <ScrollAreaPrimitive.Viewport className="h-full w-full" ref={scrollAreaRef}>
              <div className="space-y-4 p-4">
                {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  <div className="whitespace-pre-wrap break-words">
                    {message.content}
                  </div>
                  
                  {message.sqlQuery && (
                    <div className="mt-3 pt-3 border-t border-border/50">
                      <div className="flex items-center gap-2 mb-2">
                        <Code className="h-3 w-3" />
                        <span className="text-xs font-medium">SQL Query</span>
                      </div>
                      <pre className="text-xs bg-background/50 rounded p-2 overflow-x-auto">
                        <code>{message.sqlQuery}</code>
                      </pre>
                    </div>
                  )}
                  
                  {message.queryResult && formatQueryResult(message.queryResult)}
                  
                  <div className="text-xs opacity-70 mt-2">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-muted rounded-lg px-4 py-2">
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
              </div>
            </ScrollAreaPrimitive.Viewport>
            <ScrollAreaPrimitive.Scrollbar
              className="flex touch-none select-none transition-colors p-0.5 bg-transparent hover:bg-muted"
              orientation="vertical"
            >
              <ScrollAreaPrimitive.Thumb className="flex-1 bg-border rounded-full relative before:content-[''] before:absolute before:top-1/2 before:left-1/2 before:-translate-x-1/2 before:-translate-y-1/2 before:w-full before:h-full before:min-w-[44px] before:min-h-[44px]" />
            </ScrollAreaPrimitive.Scrollbar>
          </ScrollAreaPrimitive.Root>
        </div>

        <div className="flex-shrink-0">
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="flex gap-2">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your data..."
              disabled={isLoading}
              className="flex-1"
            />
            <Button type="submit" disabled={isLoading || !input.trim()}>
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </form>

          <div className="flex items-center gap-2 text-xs text-muted-foreground mt-2">
            <Database className="h-3 w-3" />
            <span>Connected to schema: {schemaName}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

