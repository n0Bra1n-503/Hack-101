export default function ErrorState({ message = 'Something went wrong.', onRetry }) {
  return (
    <div className="py-12 text-center">
      <div className="inline-block bg-critical text-ink text-sm px-3 py-1.5 rounded-md mb-3">{message}</div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-3 py-1.5 rounded-md border border-hairline text-sm text-ink hover:bg-hairline/40"
        >
          Retry
        </button>
      )}
    </div>
  )
}
