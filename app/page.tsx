"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import GeracaoDwTab from "@/components/tabs/geracao-dw-tab"
import ConfiguracaoExploracaoTab from "@/components/tabs/configuracao-exploracao-tab"
import { Database, FileSpreadsheet } from "lucide-react"

// Re-export types for compatibility
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

export default function ETLProcessor() {
  const [activeTab, setActiveTab] = useState("geracao-dw")



  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-4 text-balance">ETL Processor</h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-pretty">
            Plataforma completa para processamento de dados e exploração de Data Warehouses com interface intuitiva e ferramentas avançadas.
          </p>
        </div>

        {/* Main Content with Tabs */}
        <div className="max-w-6xl mx-auto">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-8">
              <TabsTrigger value="geracao-dw" className="flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4" />
                Geração de DW
              </TabsTrigger>
              <TabsTrigger value="configuracao-exploracao" className="flex items-center gap-2">
                <Database className="w-4 h-4" />
                Configuração de Exploração
              </TabsTrigger>
            </TabsList>

            <TabsContent value="geracao-dw" className="space-y-6">
              <GeracaoDwTab />
            </TabsContent>

            <TabsContent value="configuracao-exploracao" className="space-y-6">
              <ConfiguracaoExploracaoTab />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  )
}
