import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { deviceTreeApi } from '../api/client.js'

export default function DeviceTree() {
  const { classId } = useParams()
  const [tree, setTree] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadTree()
  }, [classId])

  const loadTree = async () => {
    try {
      setLoading(true)
      const resp = await deviceTreeApi.get(classId)
      setTree(resp.data)
      setError('')
    } catch (err) {
      console.error('Failed to load device tree:', err)
      setError('Failed to load device tree')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
        <div>Loading device tree...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '40px', color: 'var(--error-color, #dc3545)' }}>
        {error}
      </div>
    )
  }

  if (!tree) {
    return <div style={{ padding: '40px' }}>No device tree data</div>
  }

  // Build a map for quick lookup
  const nodeMap = {}
  tree.nodes.forEach(node => { nodeMap[node.id] = node })

  // Find children for each node
  const childrenMap = {}
  tree.nodes.forEach(node => {
    if (node.parent_enrollment) {
      // Find parent by enrollment
      const parent = tree.nodes.find(n => n.enrollment === node.parent_enrollment)
      if (parent) {
        childrenMap[parent.id] = childrenMap[parent.id] || []
        childrenMap[parent.id].push(node)
      }
    }
  })

  const renderNode = (node, depth = 0) => {
    const children = childrenMap[node.id] || []
    const isRoot = node.id === tree.root.id

    return (
      <div key={node.id} style={{ marginLeft: depth * 20 }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 12px',
          background: isRoot ? 'var(--primary-bg, #e3f2fd)' : (depth % 2 === 0 ? 'var(--card-bg, #fafafa)' : 'transparent'),
          borderRadius: 6,
          border: isRoot ? '2px solid var(--primary-color, #1976d2)' : '1px solid var(--border-color, #e0e0e0)',
          marginBottom: 4,
        }}>
          {/* Connection status indicator */}
          <div style={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            background: node.is_connected ? 'var(--success-color, #4caf50)' : 'var(--error-color, #dc3545)',
            flexShrink: 0,
          }} title={node.is_connected ? 'Online' : 'Offline'} />

          {/* Device type icon */}
          <span style={{ fontSize: '1.2rem' }}>
            {node.device_type === 'c6' ? '🌐' : node.device_type === 's3' ? '📡' : '👤'}
          </span>

          {/* Main info */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <strong style={{ color: 'var(--text-primary, #212121)' }}>
                {isRoot ? 'C6 Gateway (Root)' : (node.student_name || node.enrollment || `Student ${node.device_id.toString(16).toUpperCase()}`)}
              </strong>
              {node.enrollment && !isRoot && (
                <span style={{
                  fontSize: '0.75rem',
                  padding: '2px 6px',
                  background: 'var(--primary-light, #bbdefb)',
                  borderRadius: 4,
                  color: 'var(--primary-dark, #0d47a1)',
                  fontFamily: 'monospace',
                }}>
                  {node.enrollment}
                </span>
              )}
              <span style={{
                fontSize: '0.7rem',
                color: 'var(--text-muted, #757575)',
                fontFamily: 'monospace',
              }}>
                {node.device_type}
              </span>
              <span style={{
                fontSize: '0.7rem',
                color: node.is_direct ? 'var(--success-color, #4caf50)' : 'var(--warning-color, #ff9800)',
              }}>
                {node.is_direct ? 'Direct' : `Via ${node.parent_enrollment || 'Relay'}`}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 16, fontSize: '0.75rem', color: 'var(--text-secondary, #616161)', marginTop: 4 }}>
              <span>Hops: {node.hop_count}</span>
              <span>RSSI: {node.rssi} dBm</span>
              <span>Battery: {node.battery_pct}%</span>
              <span>ID: 0x{node.device_id.toString(16).toUpperCase().padStart(8, '0')}</span>
            </div>
          </div>

          {/* Expand/collapse not needed for now - always show children */}
        </div>

        {children.length > 0 && (
          <div style={{ borderLeft: '2px dashed var(--border-color, #e0e0e0)', paddingLeft: 8, marginLeft: 6 }}>
            {children.map(child => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <Link to="/dashboard" style={{ color: 'var(--primary-color, #1976d2)', textDecoration: 'none', marginRight: 16 }}>
            ← Back to Dashboard
          </Link>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Device Tree — Class {classId}</h1>
        </div>
        <button
          onClick={loadTree}
          disabled={loading}
          style={{ padding: '8px 16px', background: 'var(--primary-color, #1976d2)', color: 'white', border: 'none', borderRadius: 4, cursor: loading ? 'not-allowed' : 'pointer' }}
        >
          {loading ? 'Refreshing...' : '🔄 Refresh'}
        </button>
      </div>

      <div style={{
        background: 'var(--card-bg, #fff)',
        borderRadius: 8,
        border: '1px solid var(--border-color, #e0e0e0)',
        padding: 16,
      }}>
        <div style={{ marginBottom: 16, padding: 12, background: 'var(--info-bg, #e8f5e9)', borderRadius: 6, border: '1px solid var(--success-color, #4caf50)' }}>
          <strong>Legend:</strong>
          <span style={{ marginLeft: 16 }}>🟢 Online</span>
          <span style={{ marginLeft: 16 }}>🔴 Offline</span>
          <span style={{ marginLeft: 16 }}>🌐 C6 Gateway</span>
          <span style={{ marginLeft: 16 }}>📡 S3 Mesh Master</span>
          <span style={{ marginLeft: 16 }}>👤 Student</span>
          <span style={{ marginLeft: 16 }}>Direct = 1 hop from root</span>
          <span style={{ marginLeft: 16 }}>Relayed = 2+ hops</span>
        </div>

        {renderNode(tree.root)}
      </div>
    </div>
  )
}