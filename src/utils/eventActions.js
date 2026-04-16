const EVENT_TIME_ZONE = 'America/New_York'
const DEFAULT_EVENT_DURATION_MS = 60 * 60 * 1000
const RELATIVE_SCHEDULE_PATTERN = /\b(?:\d+\s*(?:min|mins|minute|minutes|hr|hrs|hour|hours|day|days|week|weeks|month|months|year|years)|ago|from posting|posted|remaining|left)\b/i
const DATE_LIKE_PATTERN = /\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|tomorrow)\b|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?|\d{4}-\d{2}-\d{2}/i
const TIME_LIKE_PATTERN = /\b(?:\d{1,2}(?::\d{2})?\s?(?:am|pm)|noon|midnight)\b|(?:\d{1,2}(?::\d{2})?\s?(?:am|pm)\s?[-–]\s?\d{1,2}(?::\d{2})?\s?(?:am|pm))/i

function toDate(value) {
  if (!value) return null
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

function normalizeScheduleText(value) {
  return typeof value === 'string' ? value.replace(/\s+/g, ' ').trim() : ''
}

function sanitizeFallbackDate(value) {
  const text = normalizeScheduleText(value)
  if (!text || RELATIVE_SCHEDULE_PATTERN.test(text)) return ''
  return DATE_LIKE_PATTERN.test(text) ? text : ''
}

function sanitizeFallbackTime(value) {
  const text = normalizeScheduleText(value)
  if (!text || RELATIVE_SCHEDULE_PATTERN.test(text)) return ''
  return TIME_LIKE_PATTERN.test(text) ? text : ''
}

function getNyDateParts(date) {
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: EVENT_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })

  const parts = formatter.formatToParts(date)
  return {
    year: parts.find((part) => part.type === 'year')?.value,
    month: parts.find((part) => part.type === 'month')?.value,
    day: parts.find((part) => part.type === 'day')?.value,
  }
}

function formatForGoogleCalendar(date, allDay) {
  if (allDay) {
    const { year, month, day } = getNyDateParts(date)
    return `${year}${month}${day}`
  }

  return date.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '')
}

function buildCalendarRange(event) {
  const start = toDate(event?.start_at)
  if (!start) return null

  const parsedEnd = toDate(event?.end_at)
  const end = parsedEnd && parsedEnd > start
    ? parsedEnd
    : new Date(start.getTime() + DEFAULT_EVENT_DURATION_MS)

  return {
    start,
    end,
    allDay: Boolean(event?.all_day),
  }
}

async function copyTextWithFallback(text) {
  if (navigator.clipboard?.writeText && window.isSecureContext) {
    await navigator.clipboard.writeText(text)
    return true
  }

  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', '')
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  textarea.style.pointerEvents = 'none'
  document.body.appendChild(textarea)
  textarea.focus()
  textarea.select()

  let copied = false
  try {
    copied = document.execCommand('copy')
  } finally {
    document.body.removeChild(textarea)
  }

  return copied
}

export function getEventDisplayDateTime(event) {
  const range = buildCalendarRange(event)
  if (!range) {
    return {
      dateText: sanitizeFallbackDate(event?.date),
      timeText: sanitizeFallbackTime(event?.time),
    }
  }

  const dateText = new Intl.DateTimeFormat('en-US', {
    timeZone: EVENT_TIME_ZONE,
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(range.start)

  const timeText = range.allDay
    ? 'All day'
    : new Intl.DateTimeFormat('en-US', {
        timeZone: EVENT_TIME_ZONE,
        hour: 'numeric',
        minute: '2-digit',
      }).format(range.start)

  return { dateText, timeText }
}

export function getGoogleCalendarUrl(event) {
  const range = buildCalendarRange(event)
  if (!range) return null

  const base = 'https://calendar.google.com/calendar/render?action=TEMPLATE'
  const params = new URLSearchParams()
  params.set('text', event.title || 'Untitled Event')

  const detailsParts = []
  if (event.description) detailsParts.push(event.description)
  if (event.club) detailsParts.push(`Hosted by @${event.club}`)
  if (event.source_post_permalink) detailsParts.push(`Source: ${event.source_post_permalink}`)
  if (detailsParts.length) params.set('details', detailsParts.join('\n\n'))

  if (event.location) params.set('location', event.location)

  const startStr = formatForGoogleCalendar(range.start, range.allDay)
  const endDate = range.allDay
    ? new Date(range.start.getTime() + 24 * 60 * 60 * 1000)
    : range.end
  const endStr = formatForGoogleCalendar(endDate, range.allDay)
  params.set('dates', `${startStr}/${endStr}`)

  return `${base}&${params.toString()}`
}

export async function shareEvent(event) {
  const eventUrl = `${window.location.origin}/events/${event.id}`

  if (typeof navigator.share === 'function') {
    try {
      await navigator.share({
        title: event.title,
        text: 'Check out this event on KnightLife!',
        url: eventUrl,
      })
      return 'shared'
    } catch (err) {
      if (err?.name === 'AbortError') {
        return 'aborted'
      }
      console.error('[Share] navigator.share failed:', err)
    }
  }

  try {
    const copied = await copyTextWithFallback(eventUrl)
    if (copied) return 'copied'
  } catch (err) {
    console.error('[Share] Clipboard fallback failed:', err)
  }

  window.prompt('Copy this link:', eventUrl)
  return 'prompted'
}
