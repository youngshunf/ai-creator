# Implementation Plan - Asset Inspiration Panel

## Goal
Replace the "素材灵感" (Asset Inspiration) placeholder in the Creation Center (`/creation`) with a functional panel that allows users to browse and insert assets (Images, Templates).

## Proposed Changes

### 1. Create `AssetPanel` Component
**File**: `apps/desktop/src/components/creation/AssetPanel.tsx`

**Features**:
- **Tabs**: "Images" (图片), "Templates" (模板).
- **Search Bar**: Input field to filter assets.
- **Image Grid**:
    - Display mock images from Unsplash.
    - Hover effect: "Plus" icon to insert.
- **Template List**:
    - List of text templates/quotes.
    - Click to insert into editor.

**Mock Data Strategy**:
- Use static arrays for Templates.
- Use Unsplash Source URLs (`https://source.unsplash.com/random/400x300?sig=1`) for images.

### 2. Integrate into `CreationPage`
**File**: `apps/desktop/src/routes/creation/index.tsx`

- Import `AssetPanel`.
- Render `AssetPanel` when `rightPanelTab === 'assets'`.
- Pass a `onInsert` prop to `AssetPanel`.
- Implement `handleAssetInsert(type, content)`:
    - If Image: Append `![Alt](url)` markdown to content.
    - If Text: Append text to content.

## Verification Plan

### Manual Verification
1.  **Open Creation Center**: Navigate to `/creation`.
2.  **Open Asset Panel**: Click the "素材灵感" tab in the right sidebar.
3.  **Insert Image**:
    - Click on a mock image.
    - Verify that an image markdown is inserted into the main editor (TipTap).
4.  **Insert Template**:
    - Switch to "Templates" tab.
    - Click a template.
    - Verify text is appended to the editor.
