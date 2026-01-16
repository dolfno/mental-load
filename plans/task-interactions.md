# Plan: Task User Interactions

## Overview
Enhance TaskCard with four clear user interactions: Complete, Postpone, Edit, Delete.

---

## Current State

| Interaction | Status | How it works |
|-------------|--------|--------------|
| Complete | Per-person buttons | Click member name → creates completion with member_id |
| Postpone | Not available | - |
| Edit | API only | PUT /api/tasks/{id} exists, no UI |
| Delete | API only | DELETE /api/tasks/{id} exists, no UI |

---

## Target State

| Interaction | UI | Notes |
|-------------|-----|-------|
| **Complete** | Single green "Voltooid" button | No member tracking |
| **Postpone** | "Uitstellen" button → dropdown | Morgen, 3 dagen, Week, Maand, Custom date |
| **Edit** | In overflow menu (⋮) | Opens edit form |
| **Delete** | In overflow menu (⋮) | With confirmation dialog |

### TaskCard Layout
```
+--------------------------------------------------+
| [Task Name]                          [Urgency]   |
| Recurrence info                                  |
| Due date                                         |
|                                                  |
| [✓ Voltooid]  [⏱ Uitstellen ▾]            [⋮]   |
+--------------------------------------------------+
```

---

## Implementation

### Phase 1: Simplify Complete (remove member tracking)

**Backend** (`backend/src/`)
1. `presentation/schemas.py` - Make `member_id` optional in `CompleteTaskRequest`
2. `domain/entities.py` - Make `completed_by_id` optional in `TaskCompletion`
3. `application/task_usecases.py` - Update `CompleteTask.execute()` to handle None member_id
4. `infrastructure/repositories.py` - Handle nullable completed_by_id in save

**Frontend** (`frontend/src/`)
1. `api.ts` - Update `complete()` to not require memberId
2. `components/TaskCard.tsx` - Replace member buttons with single "Voltooid" button
3. `components/TaskList.tsx` - Remove `members` prop, simplify `onComplete`
4. `components/Dashboard.tsx` - Update `handleComplete`, remove members prop from TaskList

### Phase 2: Add Postpone

**Backend**
1. `presentation/schemas.py` - Add `PostponeTaskRequest` with `new_due_date: date`
2. `application/task_usecases.py` - Add `PostponeTask` use case
3. `presentation/routes/tasks.py` - Add `POST /api/tasks/{id}/postpone` endpoint

**Frontend**
1. `api.ts` - Add `postpone(taskId, newDueDate)` method
2. `components/PostponeMenu.tsx` - New component with dropdown options:
   - Morgen (tomorrow)
   - Over 3 dagen (+3 days)
   - Volgende week (+7 days)
   - Volgende maand (+1 month)
   - Kies datum... (date picker)
3. `components/TaskCard.tsx` - Add "Uitstellen" button that opens PostponeMenu
4. `components/Dashboard.tsx` - Add `handlePostpone` handler

### Phase 3: Add Edit UI

**Backend**: No changes (PUT endpoint exists)

**Frontend**
1. `api.ts` - Add `update(taskId, data)` method
2. `components/AddTaskForm.tsx` → Refactor to `TaskForm.tsx` supporting edit mode:
   - Accept optional `task` prop for pre-population
   - Dynamic button label: "Opslaan" (edit) vs "Toevoegen" (create)
3. `components/TaskCard.tsx` - Add edit action in overflow menu
4. `components/Dashboard.tsx` - Add `editingTask` state and `handleEdit` handler

### Phase 4: Add Delete UI

**Backend**: No changes (DELETE endpoint exists)

**Frontend**
1. `components/ConfirmDialog.tsx` - New component for confirmation
2. `components/TaskCard.tsx` - Add delete action in overflow menu
3. `components/Dashboard.tsx` - Add `handleDelete` with confirmation

---

## Files to Modify

### Backend
| File | Changes |
|------|---------|
| `backend/src/presentation/schemas.py` | Optional member_id, new PostponeTaskRequest |
| `backend/src/presentation/routes/tasks.py` | Add postpone endpoint |
| `backend/src/application/task_usecases.py` | Update CompleteTask, add PostponeTask |
| `backend/src/domain/entities.py` | Optional completed_by_id |
| `backend/src/infrastructure/repositories.py` | Handle nullable completed_by_id |

### Frontend
| File | Changes |
|------|---------|
| `frontend/src/api.ts` | Simplify complete, add postpone, add update |
| `frontend/src/components/TaskCard.tsx` | New action buttons layout |
| `frontend/src/components/TaskList.tsx` | Remove members prop |
| `frontend/src/components/Dashboard.tsx` | Add all new handlers |
| `frontend/src/components/AddTaskForm.tsx` | Refactor to support edit mode |
| `frontend/src/components/PostponeMenu.tsx` | New file |
| `frontend/src/components/ConfirmDialog.tsx` | New file |

---

## Verification

1. **Complete**: Click "Voltooid" → task moves to next due date, completion recorded
2. **Postpone**: Click "Uitstellen" → select option → next_due updates to selected date
3. **Edit**: Click ⋮ → "Bewerken" → form opens with current values → save updates task
4. **Delete**: Click ⋮ → "Verwijderen" → confirm → task disappears from list
5. Run backend tests: `cd backend && pytest`
6. Verify UI responsiveness on mobile viewport

---

## Implementation Summary

### Backend Changes
- **`schemas.py`**: Made `member_id` optional in `CompleteTaskRequest` and `completed_by_id` optional in `TaskCompletionResponse`
- **`entities.py`**: Made `completed_by_id` optional in `TaskCompletion` dataclass
- **`task_usecases.py`**: Updated `CompleteTask.execute()` to accept optional `member_id`
- **`routes/tasks.py`**: Updated complete endpoint to handle optional request body

### Frontend Changes
- **`api.ts`**:
  - Simplified `complete()` to not require memberId
  - Added `update()` and `postpone()` methods
- **`types.ts`**: Added `TaskUpdateRequest` interface
- **`TaskCard.tsx`**: Complete rewrite with:
  - Single green "Voltooid" button for completion
  - Blue "Uitstellen" dropdown with preset options (Morgen, Over 3 dagen, Volgende week, Volgende maand) and custom date picker
  - Overflow menu (⋮) with "Bewerken" and "Verwijderen" options
  - Delete confirmation dialog overlay
- **`TaskList.tsx`**: Updated props to remove `members`, added new handlers
- **`TaskForm.tsx`**: New component (refactored from `AddTaskForm.tsx`) supporting both create and edit modes
- **`Dashboard.tsx`**: Added handlers for all interactions: `handleComplete`, `handlePostpone`, `handleEdit`, `handleDelete`, `handleUpdateTask`

### Deviations from Plan
- **Postpone**: Used existing `PUT /api/tasks/{id}` endpoint with `next_due` instead of creating a separate `/postpone` endpoint
- **PostponeMenu**: Integrated directly into `TaskCard.tsx` instead of separate component
- **ConfirmDialog**: Implemented as inline overlay in `TaskCard.tsx` instead of separate component

### Test Results
- All 56 backend tests pass
- Frontend builds successfully with no TypeScript errors
