import type { CSVData, FieldConfig } from "@/app/page"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'

export interface TransformRequest {
  csvContent: string
  fields: FieldConfig[]
  tableName: string
  delimiter: string
  databaseType: string
  includeCreateTable: boolean
}

export interface TransformResponse {
  success: boolean
  sql: string
  rowsProcessed: number
  fieldsSelected: number
  error?: string
}

export class ApiService {
  private static async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }

    return response.json()
  }

  static async healthCheck(): Promise<{ status: string; service: string }> {
    return this.makeRequest('/api/health')
  }

  static async transformCsvToSql(request: TransformRequest): Promise<TransformResponse> {
    return this.makeRequest('/api/transform', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  static csvDataToString(csvData: CSVData, delimiter: string): string {
    const escapeField = (field: string) => {
      if (field.includes(delimiter) || field.includes('"') || field.includes('\n')) {
        return `"${field.replace(/"/g, '""')}"`
      }
      return field
    }

    const headerRow = csvData.headers.map(escapeField).join(delimiter)
    const dataRows = csvData.rows.map(row =>
      row.map(escapeField).join(delimiter)
    )

    return [headerRow, ...dataRows].join('\n')
  }

  // Data Warehouse API methods
  static async analyzeSql(sql: string): Promise<any> {
    return this.makeRequest('/api/analyze-sql', {
      method: 'POST',
      body: JSON.stringify({ sql }),
    })
  }

  static async generateDwModel(options: {
    sql: string
    model_name?: string
    include_indexes?: boolean
    include_partitioning?: boolean
    csv_data?: any
  }): Promise<any> {
    return this.makeRequest('/api/generate-dw-model', {
      method: 'POST',
      body: JSON.stringify({
        sql: options.sql,
        model_name: options.model_name || 'DataWarehouse',
        include_indexes: options.include_indexes ?? true,
        include_partitioning: options.include_partitioning ?? false,
        csv_data: options.csv_data,
      }),
    })
  }

  static async getDwRecommendations(starSchema: any): Promise<any> {
    return this.makeRequest('/api/dw-recommendations', {
      method: 'POST',
      body: JSON.stringify({ star_schema: starSchema }),
    })
  }

  static async getDwMetadata(): Promise<any> {
    return this.makeRequest('/api/dw-metadata')
  }

  // NLQ Session Management API methods
  static async createNlqSession(metadata?: any): Promise<any> {
    return this.makeRequest('/api/nlq/session/create', {
      method: 'POST',
      body: JSON.stringify({ metadata: metadata || {} }),
    })
  }

  static async provisionNlqSession(schemaId: string, sqlContent: string): Promise<any> {
    return this.makeRequest(`/api/nlq/session/${schemaId}/provision`, {
      method: 'POST',
      body: JSON.stringify({ sql: sqlContent }),
    })
  }

  static async getNlqSessionInfo(schemaId: string): Promise<any> {
    return this.makeRequest(`/api/nlq/session/${schemaId}/info`)
  }

  static async cleanupNlqSession(schemaId: string): Promise<any> {
    return this.makeRequest(`/api/nlq/session/${schemaId}/cleanup`, {
      method: 'DELETE',
    })
  }

  static async forceCleanupSessions(): Promise<any> {
    return this.makeRequest('/api/nlq/cleanup/force', {
      method: 'POST',
    })
  }

  static async checkDatabaseHealth(): Promise<any> {
    return this.makeRequest('/api/database/health')
  }
}
