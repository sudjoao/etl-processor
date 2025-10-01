"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, Database, Table, Key, BarChart3, Settings, Download, Eye } from "lucide-react"
import { ApiService } from "@/lib/api"

interface DataWarehouseViewerProps {
  sqlContent: string
  onClose?: () => void
}

interface StarSchema {
  name: string
  fact_table: {
    name: string
    source_table: string
    measures: string[]
    dimension_keys: string[]
    grain: string
    description: string
  }
  dimension_tables: Array<{
    name: string
    source_table: string
    surrogate_key: string
    natural_key: string
    attributes: string[]
    scd_type: number
    description: string
  }>
  relationships: Array<{
    from_table: string
    from_column: string
    to_table: string
    to_column: string
    relationship_type: string
  }>
  metadata: {
    created_at: string
    modeling_approach: string
    source_tables: number
  }
}

export function DataWarehouseViewer({ sqlContent, onClose }: DataWarehouseViewerProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dwModel, setDwModel] = useState<any>(null)
  const [recommendations, setRecommendations] = useState<any>(null)
  const [activeTab, setActiveTab] = useState("overview")

  useEffect(() => {
    if (sqlContent) {
      generateDwModel()
    }
  }, [sqlContent])

  const generateDwModel = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await ApiService.generateDwModel({
        sql: sqlContent,
        model_name: 'DataWarehouse',
        dialect: 'mysql',
        include_indexes: true,
        include_partitioning: false
      })

      setDwModel(result)

      // Get recommendations
      if (result.star_schema) {
        const recResult = await ApiService.getDwRecommendations(result.star_schema)
        setRecommendations(recResult)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate DW model')
    } finally {
      setLoading(false)
    }
  }

  const downloadDdl = () => {
    if (!dwModel?.ddl_statements) return

    const ddlContent = dwModel.ddl_statements.join('\n\n')
    const blob = new Blob([ddlContent], { type: 'text/sql' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${dwModel.star_schema?.name || 'datawarehouse'}_schema.sql`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const downloadDml = () => {
    if (!dwModel?.dml_statements) return

    // Convert DML statements object to string
    const dmlContent = Object.values(dwModel.dml_statements).join('\n\n')
    const blob = new Blob([dmlContent], { type: 'text/sql' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${dwModel.star_schema?.name || 'datawarehouse'}_sample_data.sql`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const downloadComplete = () => {
    if (!dwModel?.ddl_statements && !dwModel?.dml_statements) return

    let content = ''

    // Add DDL first
    if (dwModel.ddl_statements) {
      content += '-- ========================================\n'
      content += '-- DDL STATEMENTS (CREATE TABLES)\n'
      content += '-- ========================================\n\n'
      content += dwModel.ddl_statements.join('\n\n')
      content += '\n\n'
    }

    // Add DML after
    if (dwModel.dml_statements) {
      content += '-- ========================================\n'
      content += '-- DML STATEMENTS (SAMPLE DATA)\n'
      content += '-- ========================================\n\n'
      content += Object.values(dwModel.dml_statements).join('\n\n')
    }

    const blob = new Blob([content], { type: 'text/sql' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${dwModel.star_schema?.name || 'datawarehouse'}_complete.sql`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="flex items-center justify-center p-8">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span>Generating Data Warehouse model...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="w-full">
        <CardContent className="p-6">
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <div className="mt-4 flex space-x-2">
            <Button onClick={generateDwModel} variant="outline">
              Try Again
            </Button>
            {onClose && (
              <Button onClick={onClose} variant="ghost">
                Close
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!dwModel) {
    return null
  }

  const starSchema: StarSchema = dwModel.star_schema

  return (
    <div className="w-full space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Database className="h-6 w-6" />
            {starSchema.name}
          </h2>
          <p className="text-muted-foreground">
            Star schema with {starSchema.dimension_tables.length} dimensions and 1 fact table
          </p>
        </div>
        <div className="flex space-x-2">
          <Button onClick={downloadDdl} variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Download DDL
          </Button>
          {dwModel?.dml_statements && (
            <Button onClick={downloadDml} variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Download DML
            </Button>
          )}
          {(dwModel?.ddl_statements || dwModel?.dml_statements) && (
            <Button onClick={downloadComplete} variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Download Complete
            </Button>
          )}
          {onClose && (
            <Button onClick={onClose} variant="ghost" size="sm">
              Close
            </Button>
          )}
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="fact">Fact Table</TabsTrigger>
          <TabsTrigger value="dimensions">Dimensions</TabsTrigger>
          <TabsTrigger value="ddl">DDL Scripts</TabsTrigger>
          <TabsTrigger value="dml">Sample Data</TabsTrigger>
          <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Fact Table</CardTitle>
                <Table className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">1</div>
                <p className="text-xs text-muted-foreground">
                  {starSchema.fact_table.measures.length} measures
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Dimensions</CardTitle>
                <Key className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{starSchema.dimension_tables.length}</div>
                <p className="text-xs text-muted-foreground">
                  Including time dimension
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Source Tables</CardTitle>
                <Database className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{starSchema.metadata.source_tables}</div>
                <p className="text-xs text-muted-foreground">
                  {starSchema.metadata.modeling_approach} approach
                </p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Schema Visualization</CardTitle>
              <CardDescription>
                Star schema structure showing relationships between fact and dimension tables
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center space-y-6 p-6">
                {/* Fact Table in Center */}
                <div className="bg-blue-100 border-2 border-blue-300 rounded-lg p-4 text-center">
                  <div className="font-bold text-blue-800">{starSchema.fact_table.name}</div>
                  <div className="text-sm text-blue-600 mt-1">
                    {starSchema.fact_table.measures.length} measures
                  </div>
                  <div className="text-xs text-blue-500 mt-1">
                    {starSchema.fact_table.grain}
                  </div>
                </div>

                {/* Dimension Tables Around */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 w-full">
                  {starSchema.dimension_tables.map((dim, index) => (
                    <div key={index} className="bg-green-100 border-2 border-green-300 rounded-lg p-3 text-center">
                      <div className="font-bold text-green-800">{dim.name}</div>
                      <div className="text-sm text-green-600 mt-1">
                        {dim.attributes.length} attributes
                      </div>
                      <div className="text-xs text-green-500 mt-1">
                        SCD Type {dim.scd_type}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="fact" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                {starSchema.fact_table.name}
              </CardTitle>
              <CardDescription>{starSchema.fact_table.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-semibold mb-2">Business Grain</h4>
                <p className="text-sm text-muted-foreground">{starSchema.fact_table.grain}</p>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Measures ({starSchema.fact_table.measures.length})</h4>
                <div className="flex flex-wrap gap-2">
                  {starSchema.fact_table.measures.map((measure, index) => (
                    <Badge key={index} variant="secondary">
                      {measure}
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Dimension Keys ({starSchema.fact_table.dimension_keys.length})</h4>
                <div className="flex flex-wrap gap-2">
                  {starSchema.fact_table.dimension_keys.map((key, index) => (
                    <Badge key={index} variant="outline">
                      {key}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="dimensions" className="space-y-4">
          {starSchema.dimension_tables.map((dim, index) => (
            <Card key={index}>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Key className="h-5 w-5" />
                  {dim.name}
                </CardTitle>
                <CardDescription>{dim.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h5 className="font-medium mb-1">Source Table</h5>
                    <p className="text-sm text-muted-foreground">{dim.source_table}</p>
                  </div>
                  <div>
                    <h5 className="font-medium mb-1">SCD Type</h5>
                    <Badge variant={dim.scd_type === 2 ? "default" : "secondary"}>
                      Type {dim.scd_type}
                    </Badge>
                  </div>
                </div>

                <div>
                  <h5 className="font-medium mb-2">Attributes ({dim.attributes.length})</h5>
                  <div className="flex flex-wrap gap-2">
                    {dim.attributes.map((attr, attrIndex) => (
                      <Badge 
                        key={attrIndex} 
                        variant={attr === dim.natural_key ? "default" : "outline"}
                      >
                        {attr}
                        {attr === dim.natural_key && " (NK)"}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="ddl" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>DDL Scripts</CardTitle>
              <CardDescription>
                Generated SQL DDL statements for creating the star schema
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {dwModel.ddl_statements?.map((ddl: string, index: number) => (
                  <div key={index} className="bg-muted p-4 rounded-lg">
                    <pre className="text-sm overflow-x-auto whitespace-pre-wrap">
                      {ddl}
                    </pre>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="dml" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Sample Data (DML)</CardTitle>
              <CardDescription>
                Generated SQL INSERT statements with sample data for testing the star schema
              </CardDescription>
            </CardHeader>
            <CardContent>
              {dwModel.dml_statements ? (
                <div className="space-y-4">
                  {Object.entries(dwModel.dml_statements).map(([tableName, dml]: [string, any], index: number) => (
                    <div key={index} className="space-y-2">
                      <h4 className="font-medium text-sm text-muted-foreground">
                        {tableName.replace('insert_', '').replace(/_/g, ' ').toUpperCase()}
                      </h4>
                      <div className="bg-muted p-4 rounded-lg">
                        <pre className="text-sm overflow-x-auto whitespace-pre-wrap">
                          {dml}
                        </pre>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <Alert>
                  <AlertDescription>
                    No sample data available. DML generation may have been disabled.
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="recommendations" className="space-y-4">
          {recommendations && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="h-5 w-5" />
                    Model Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h5 className="font-medium mb-1">Complexity Score</h5>
                      <div className="text-2xl font-bold">{recommendations.complexity_score}</div>
                    </div>
                    <div>
                      <h5 className="font-medium mb-1">Complexity Level</h5>
                      <Badge variant={
                        recommendations.complexity_level === 'high' ? 'destructive' :
                        recommendations.complexity_level === 'medium' ? 'default' : 'secondary'
                      }>
                        {recommendations.complexity_level}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {Object.entries(recommendations.recommendations || {}).map(([category, items]: [string, any]) => (
                <Card key={category}>
                  <CardHeader>
                    <CardTitle className="capitalize">{category.replace('_', ' ')}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {items.map((item: string, index: number) => (
                        <li key={index} className="text-sm flex items-start gap-2">
                          <span className="text-muted-foreground">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
