import { useState } from 'react'
import Hero from '../components/Hero'
import ClubGrid from '../components/ClubGrid'
import { clubs } from '../data/clubs'

export default function Home() {
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all')

  const categories = ['all', ...new Set(clubs.flatMap((c) => c.tags))]

  const filtered = clubs.filter((club) => {
    const matchSearch =
      !search ||
      club.name.toLowerCase().includes(search.toLowerCase()) ||
      club.description.toLowerCase().includes(search.toLowerCase()) ||
      club.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()))
    const matchCategory = category === 'all' || club.tags.includes(category)
    return matchSearch && matchCategory
  })

  return (
    <>
      <Hero onSearchChange={setSearch} searchValue={search} />
      <ClubGrid
        clubs={filtered}
        categories={categories}
        category={category}
        onCategoryChange={setCategory}
      />
    </>
  )
}
