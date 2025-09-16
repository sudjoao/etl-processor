"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { DragDropContext, Droppable, Draggable, type DropResult } from "@hello-pangea/dnd"
import { GripVertical, Eye, EyeOff, ArrowUp, ArrowDown, CheckSquare, Square } from "lucide-react"
import type { FieldConfig } from "@/app/page"

interface FieldSelectorProps {
  headers: string[]
  fields: FieldConfig[]
  onFieldsChange: (fields: FieldConfig[]) => void
}

export function FieldSelector({ headers, fields, onFieldsChange }: FieldSelectorProps) {
  const [localFields, setLocalFields] = useState<FieldConfig[]>([])

  // Initialize fields from headers
  useEffect(() => {
    if (fields.length === 0 && headers.length > 0) {
      const initialFields = headers.map((header, index) => ({
        name: header,
        selected: true, // Select all by default
        order: index,
        format: "text" as const,
      }))
      setLocalFields(initialFields)
    } else {
      setLocalFields(fields)
    }
  }, [headers, fields])

  const handleFieldToggle = (fieldName: string) => {
    setLocalFields((prev) =>
      prev.map((field) => (field.name === fieldName ? { ...field, selected: !field.selected } : field)),
    )
  }

  const handleSelectAll = () => {
    const allSelected = localFields.every((field) => field.selected)
    setLocalFields((prev) => prev.map((field) => ({ ...field, selected: !allSelected })))
  }

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return

    const items = Array.from(localFields)
    const [reorderedItem] = items.splice(result.source.index, 1)
    items.splice(result.destination.index, 0, reorderedItem)

    // Update order property
    const updatedItems = items.map((item, index) => ({ ...item, order: index }))
    setLocalFields(updatedItems)
  }

  const moveField = (index: number, direction: "up" | "down") => {
    const newFields = [...localFields]
    const targetIndex = direction === "up" ? index - 1 : index + 1

    if (targetIndex < 0 || targetIndex >= newFields.length) return // Swap fields
    ;[newFields[index], newFields[targetIndex]] = [newFields[targetIndex], newFields[index]]

    // Update order
    const updatedFields = newFields.map((field, idx) => ({ ...field, order: idx }))
    setLocalFields(updatedFields)
  }

  const handleConfirm = () => {
    onFieldsChange(localFields)
  }

  const selectedCount = localFields.filter((field) => field.selected).length
  const allSelected = localFields.length > 0 && localFields.every((field) => field.selected)
  const someSelected = localFields.some((field) => field.selected)

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" size="sm" onClick={handleSelectAll}>
            {allSelected ? (
              <>
                <Square className="w-4 h-4 mr-2" />
                Desmarcar Todos
              </>
            ) : (
              <>
                <CheckSquare className="w-4 h-4 mr-2" />
                Selecionar Todos
              </>
            )}
          </Button>
          <Badge variant="secondary">
            {selectedCount} de {localFields.length} campos selecionados
          </Badge>
        </div>
      </div>

      {/* Field List */}
      <Card>
        <CardContent className="p-0">
          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="fields">
              {(provided, snapshot) => (
                <div
                  {...provided.droppableProps}
                  ref={provided.innerRef}
                  className={`min-h-[200px] ${snapshot.isDraggingOver ? "bg-primary/5" : ""}`}
                >
                  {localFields.map((field, index) => (
                    <Draggable key={field.name} draggableId={field.name} index={index}>
                      {(provided, snapshot) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          className={`
                            flex items-center space-x-4 p-4 border-b last:border-b-0 transition-colors
                            ${snapshot.isDragging ? "bg-primary/10 shadow-lg" : "hover:bg-muted/50"}
                            ${field.selected ? "" : "opacity-60"}
                          `}
                        >
                          {/* Drag Handle */}
                          <div {...provided.dragHandleProps} className="cursor-grab active:cursor-grabbing">
                            <GripVertical className="w-4 h-4 text-muted-foreground" />
                          </div>

                          {/* Checkbox */}
                          <Checkbox
                            checked={field.selected}
                            onCheckedChange={() => handleFieldToggle(field.name)}
                            className="data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                          />

                          {/* Field Info */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2">
                              <h3 className="font-medium truncate">{field.name}</h3>
                              <Badge variant="outline" className="text-xs">
                                {field.format}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground">Posição: {index + 1}</p>
                          </div>

                          {/* Visibility Icon */}
                          <div className="flex items-center space-x-2">
                            {field.selected ? (
                              <Eye className="w-4 h-4 text-primary" />
                            ) : (
                              <EyeOff className="w-4 h-4 text-muted-foreground" />
                            )}

                            {/* Move Buttons */}
                            <div className="flex flex-col">
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                                onClick={() => moveField(index, "up")}
                                disabled={index === 0}
                              >
                                <ArrowUp className="w-3 h-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0"
                                onClick={() => moveField(index, "down")}
                                disabled={index === localFields.length - 1}
                              >
                                <ArrowDown className="w-3 h-3" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        </CardContent>
      </Card>

      {/* Instructions */}
      <Alert>
        <AlertDescription>
          <strong>Dica:</strong> Arraste os campos para reordená-los, use as setas para mover um por vez, ou
          marque/desmarque para incluir no arquivo final.
        </AlertDescription>
      </Alert>

      {/* Confirm Button */}
      <div className="flex justify-between items-center">
        <div className="text-sm text-muted-foreground">
          {selectedCount === 0 && "Selecione pelo menos um campo para continuar"}
        </div>
        <Button onClick={handleConfirm} disabled={selectedCount === 0}>
          Confirmar Seleção ({selectedCount} campos)
        </Button>
      </div>
    </div>
  )
}
