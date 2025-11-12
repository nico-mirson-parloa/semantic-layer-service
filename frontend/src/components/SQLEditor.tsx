import React, { useState, useRef, useEffect, useCallback } from 'react';
import { getSQLAutocomplete } from '../services/api';
import { debounce } from 'lodash';

interface SQLEditorProps {
  value: string;
  onChange: (value: string) => void;
  onExecute?: () => void;
}

interface Suggestion {
  value: string;
  type: 'catalog' | 'schema' | 'table' | 'keyword';
  display?: string;
}

export function SQLEditor({ value, onChange, onExecute }: SQLEditorProps) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [cursorPosition, setCursorPosition] = useState(0);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Get the current word being typed
  const getCurrentWord = (text: string, position: number): { word: string; start: number } => {
    // Find word boundaries (space, newline, or SQL operators)
    const wordBoundaries = /[\s\n,;()]/;
    
    let start = position;
    while (start > 0 && !wordBoundaries.test(text[start - 1])) {
      start--;
    }
    
    let end = position;
    while (end < text.length && !wordBoundaries.test(text[end])) {
      end++;
    }
    
    return {
      word: text.substring(start, end),
      start
    };
  };

  // Fetch autocomplete suggestions
  const fetchSuggestions = useCallback(
    debounce(async (searchTerm: string) => {
      if (!searchTerm && !searchTerm.includes('.')) {
        setShowSuggestions(false);
        return;
      }

      try {
        const result = await getSQLAutocomplete(searchTerm);
        const allSuggestions: Suggestion[] = [];

        // Add catalogs
        result.suggestions.catalogs?.forEach((catalog: string) => {
          allSuggestions.push({ value: catalog, type: 'catalog' });
        });

        // Add schemas
        result.suggestions.schemas?.forEach((schema: string) => {
          allSuggestions.push({ value: schema, type: 'schema' });
        });

        // Add tables
        result.suggestions.tables?.forEach((table: any) => {
          allSuggestions.push({
            value: table.name || table,
            type: 'table',
            display: table.display || table.name || table
          });
        });

        // Add keywords
        result.suggestions.keywords?.forEach((keyword: string) => {
          allSuggestions.push({ value: keyword, type: 'keyword' });
        });

        setSuggestions(allSuggestions);
        setShowSuggestions(allSuggestions.length > 0);
        setSelectedIndex(0);
      } catch (error) {
        console.error('Failed to fetch suggestions:', error);
        setShowSuggestions(false);
      }
    }, 300),
    []
  );

  // Handle text changes
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    const position = e.target.selectionStart;
    
    onChange(newValue);
    setCursorPosition(position);
    
    // Get current word for autocomplete
    const { word } = getCurrentWord(newValue, position);
    
    // Get context (everything before current word)
    const beforeCursor = newValue.substring(0, position);
    const lastDotIndex = beforeCursor.lastIndexOf('.');
    
    let searchTerm = word;
    if (lastDotIndex !== -1 && lastDotIndex > beforeCursor.lastIndexOf(' ')) {
      // Include the catalog.schema. prefix if typing after a dot
      const start = beforeCursor.lastIndexOf(' ', lastDotIndex) + 1;
      searchTerm = beforeCursor.substring(start);
    }
    
    fetchSuggestions(searchTerm);
  };

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (!showSuggestions) {
      // Handle Cmd/Ctrl + Enter to execute
      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && onExecute) {
        e.preventDefault();
        onExecute();
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % suggestions.length);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + suggestions.length) % suggestions.length);
        break;
      case 'Enter':
        e.preventDefault();
        if (suggestions[selectedIndex]) {
          insertSuggestion(suggestions[selectedIndex]);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        break;
      case 'Tab':
        if (suggestions.length > 0) {
          e.preventDefault();
          insertSuggestion(suggestions[selectedIndex]);
        }
        break;
    }
  };

  // Insert selected suggestion
  const insertSuggestion = (suggestion: Suggestion) => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const { word, start } = getCurrentWord(value, cursorPosition);
    const before = value.substring(0, start);
    const after = value.substring(start + word.length);
    
    let insertValue = suggestion.value;
    
    // Add a space after keywords
    if (suggestion.type === 'keyword') {
      insertValue += ' ';
    }
    
    const newValue = before + insertValue + after;
    onChange(newValue);
    
    // Set cursor position after inserted text
    const newPosition = start + insertValue.length;
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(newPosition, newPosition);
    }, 0);
    
    setShowSuggestions(false);
  };

  // Click handler for suggestions
  const handleSuggestionClick = (suggestion: Suggestion) => {
    insertSuggestion(suggestion);
  };

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        textareaRef.current &&
        !textareaRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className="relative">
      <textarea
        ref={textareaRef}
        id="query"
        rows={10}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm font-mono"
        placeholder="SELECT * FROM catalog.schema.table"
        spellCheck={false}
      />
      
      {/* Autocomplete suggestions */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm"
        >
          {suggestions.map((suggestion, index) => (
            <div
              key={`${suggestion.type}-${suggestion.value}-${index}`}
              className={`cursor-pointer select-none py-2 px-3 ${
                index === selectedIndex
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-900 hover:bg-gray-100'
              }`}
              onClick={() => handleSuggestionClick(suggestion)}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono">
                  {suggestion.display || suggestion.value}
                </span>
                <span
                  className={`ml-3 text-xs ${
                    index === selectedIndex ? 'text-indigo-200' : 'text-gray-500'
                  }`}
                >
                  {suggestion.type}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
      
      <div className="mt-2 text-xs text-gray-500">
        Press Tab or Enter to autocomplete • Cmd/Ctrl + Enter to execute
      </div>
    </div>
  );
}
