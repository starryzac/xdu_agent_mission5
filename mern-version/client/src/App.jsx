import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import PromptList from './pages/PromptList';
import PromptDetail from './pages/PromptDetail';
import PromptForm from './pages/PromptForm';
import TagList from './pages/TagList';
import TagDetail from './pages/TagDetail';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/prompts" replace />} />
        <Route path="/prompts" element={<PromptList />} />
        <Route path="/prompts/new" element={<PromptForm />} />
        <Route path="/prompts/:id" element={<PromptDetail />} />
        <Route path="/prompts/:id/edit" element={<PromptForm />} />
        <Route path="/tags" element={<TagList />} />
        <Route path="/tags/:id" element={<TagDetail />} />
      </Routes>
    </BrowserRouter>
  );
}
