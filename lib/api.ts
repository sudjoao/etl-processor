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
    dialect?: string
    include_indexes?: boolean
    include_partitioning?: boolean
  }): Promise<any> {
    return this.makeRequest('/api/generate-dw-model', {
      method: 'POST',
      body: JSON.stringify({
        sql: options.sql,
        model_name: options.model_name || 'DataWarehouse',
        dialect: options.dialect || 'mysql',
        include_indexes: options.include_indexes ?? true,
        include_partitioning: options.include_partitioning ?? false,
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
}
