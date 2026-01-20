import { useEffect, useRef, useCallback } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCloseAttempt?: () => boolean; // Return false to prevent close
  title?: string;
  children: React.ReactNode;
}

export function Modal({ isOpen, onClose, onCloseAttempt, title, children }: ModalProps) {
  const overlayRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleClose = useCallback(() => {
    if (onCloseAttempt) {
      if (onCloseAttempt()) {
        onClose();
      }
    } else {
      onClose();
    }
  }, [onClose, onCloseAttempt]);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, handleClose]);

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === overlayRef.current) {
      handleClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      ref={overlayRef}
      onClick={handleOverlayClick}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
    >
      <div
        ref={contentRef}
        className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto"
        role="dialog"
        aria-modal="true"
      >
        {title && (
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <h2 className="text-xl font-semibold text-gray-800">{title}</h2>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Sluiten"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
        <div className={title ? '' : 'relative'}>
          {!title && (
            <button
              onClick={handleClose}
              className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors z-10"
              aria-label="Sluiten"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
          {children}
        </div>
      </div>
    </div>
  );
}
