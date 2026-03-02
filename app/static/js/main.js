document.addEventListener('DOMContentLoaded', () => {
    const searchBtn = document.getElementById('searchBtn');
    const searchInput = document.getElementById('searchInput');
    const resultsTable = document.getElementById('resultsTable');
    const resultsBody = document.getElementById('resultsBody');
    const loader = document.getElementById('loader');
    const emptyState = document.getElementById('empty-state');
    const btnText = document.getElementById('btnText');

    const statsContainer = document.getElementById('statsContainer');
    const minPriceEl = document.getElementById('minPrice');
    const maxPriceEl = document.getElementById('maxPrice');
    const avgPriceEl = document.getElementById('avgPrice');

    const searchAction = async () => {
        const query = searchInput.value.trim();
        if (!query) return;

        // Show loading
        loader.style.display = 'block';
        resultsTable.style.display = 'none';
        statsContainer.style.display = 'none';
        emptyState.style.display = 'none';
        searchBtn.disabled = true;
        btnText.textContent = 'Buscando...';

        try {
            const response = await fetch(`/api/search?query=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error('Error en el servidor');

            const results = await response.json();

            resultsBody.innerHTML = '';

            if (results.length === 0) {
                emptyState.style.display = 'block';
                emptyState.querySelector('p').textContent = 'No se encontraron resultados.';
            } else {
                // Calculate Stats
                const prices = results.map(item => parseFloat(item.price)).filter(p => !isNaN(p) && p > 0);

                if (prices.length > 0) {
                    const minPrice = Math.min(...prices);
                    const maxPrice = Math.max(...prices);
                    const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;

                    minPriceEl.textContent = `$${minPrice.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
                    maxPriceEl.textContent = `$${maxPrice.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
                    avgPriceEl.textContent = `$${avgPrice.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;

                    statsContainer.style.display = 'grid';
                }

                results.forEach(item => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
    <td colspan="3" style="padding:0;">
        <div style="
            max-height: 80px;
            overflow-y: auto;
            padding: 10px;
        ">
            
            <div style="
                display: grid;
                grid-template-columns: 2fr 1fr 120px;
                align-items: center;
                gap: 10px;
            ">
                
                <div style="font-weight: 500; text-align: left;">
                    ${item.name}
                </div>
                
                <div class="price-tag" style="text-align: right;">
                    $${item.price}
                </div>
                
                <div style="text-align: right;">
                    <a href="${item.link}" target="_blank"
                       style="
                           color:var(--primary);
                           text-decoration:none;
                           font-size:0.875rem;
                           border: 1px solid var(--primary);
                           padding: 4px 12px;
                           border-radius: 6px;
                           transition:0.2s;
                           display:inline-block;
                       "
                       onmouseover="this.style.background='var(--primary)';this.style.color='white'"
                       onmouseout="this.style.background='transparent';this.style.color='var(--primary)'">
                       Ver más
                    </a>
                </div>
                
            </div>

        </div>
    </td>
`;
                    resultsBody.appendChild(tr);
                });
                resultsTable.style.display = 'block';
            }
            if (window.lucide) window.lucide.createIcons();
        } catch (error) {
            console.error('Search error:', error);
            alert('Error al realizar la búsqueda. Verifique la conexión.');
            emptyState.style.display = 'block';
        } finally {
            loader.style.display = 'none';
            searchBtn.disabled = false;
            btnText.textContent = 'Buscar productos';
        }
    };

    searchBtn.addEventListener('click', searchAction);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchAction();
    });
});
