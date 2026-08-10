import React from 'react';
import { useState, useEffect } from 'react';

function App() {
    //Search Functionality
    const [movie, setMovie] = useState("")
    const [result, setResult] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    async function lookup(e) {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const res = await fetch("http://localhost:8000/search", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ movie: movie }),
            });
            if (!res.ok) throw new Error(`server returned ${res.status}`);
            const data = await res.json();
            setResult(data.result);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div>
            <div>
                <h1 class="text-left">
                    <span class="text-2xl ml-10">Cinemantic</span>
                    <span class="text-lg ml-70">Home</span>
                    <span class="text-lg ml-10">Discover</span>
                    <span class="text-lg ml-10">Genres</span>
                    <span class="text-lg ml-10">Watchlist</span>
                    <span class="text-lg ml-10">About</span>
                </h1>
            </div>
            <div class="text-left ml-25">
                <div>
                <h1>Cinemantic</h1>
                <b>Semantic search movie recommendator</b>
                <p>Find movies you'll love based on meaning, mood,
                <br />and what you're in the mood for.</p>
                </div>
                    <form onSubmit={lookup}>
                    {/* Search Box */}
                    <h2>Dynamic Product Search</h2>
                    <input
                    value={movie}
                    onChange={(e) => setMovie(e.target.value)} 
                    placeholder="Type in a movie..."
                    />
                    <button type="submit" disabled={loading || !movie}>
                        {loading ? "Loading..." : "Check"}
                    </button>
                </form>

                {error && <p>Error: {error}</p>}
                {result !== null && <p>It's {result}</p>}
            </div>
        </div>
    );
}

export default App