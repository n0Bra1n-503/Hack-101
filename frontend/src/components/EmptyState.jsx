export default function EmptyState({ message = 'Nothing here yet.' }) {
  return <div className="py-12 text-center text-inkMuted text-sm">{message}</div>
}
