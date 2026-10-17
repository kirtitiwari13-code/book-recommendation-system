// --- STATUS UPDATE (CONNECTED TO FLASK DB) ---
document.addEventListener('DOMContentLoaded', () => {

    const statusDropdown = document.getElementById('book-status');

    if (statusDropdown) {
        const isbn = window.location.pathname.split('/').pop();

        statusDropdown.addEventListener('change', (e) => {
            fetch('/update_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `isbn=${isbn}&status=${e.target.value}`
            })
            .then(res => res.text())
            .then(data => {
                alert("Status saved!");
            });
        });
    }

});
// --- PART 3: RECOMMENDATIONS ---
function getRecs(bookTitle) {
    const listDiv = document.getElementById('recommendation-list');
    listDiv.innerHTML = "<p>🔍 Finding similar posters...</p>";

    fetch(`/recommend?title=${encodeURIComponent(bookTitle)}`)
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                listDiv.innerHTML = "<p>No recommendations found.</p>";
                return;
            }
            
            let html = "<h3>People also liked:</h3>";
            html += "<div style='display: flex; flex-wrap: wrap; gap: 20px; margin-top: 20px;'>";
            
            data.forEach(book => {
                html += `
                    <div style="width: 120px; text-align: center; position: relative;">
                        <a href="/book/${book.ISBN}" style="text-decoration: none; color: black;">
                            <div style="position: relative; width: 120px; height: 180px; background: #eee; border-radius: 5px; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                                <img src="${book['Image-URL-M']}" 
                                     onerror="this.style.visibility='hidden'; this.nextElementSibling.style.display='flex';" 
                                     style="width: 100%; height: 100%; object-fit: cover; position: absolute; top: 0; left: 0; z-index: 2;">
                                
                                <div style="display: none; width: 100%; height: 100%; background: #333; color: white; font-size: 0.6rem; padding: 10px; flex-direction: column; align-items: center; justify-content: center; z-index: 1;">
                                    <span>📖</span>
                                    <p style="margin-top: 5px;">COVER NOT FOUND</p>
                                </div>
                            </div>
                            <p style="font-size: 0.7rem; margin-top: 5px; font-weight: bold;">
                                ${book['Book-Title'].substring(0, 25)}...
                            </p>
                        </a>
                    </div>`;
            });
            
            html += "</div>";
            listDiv.innerHTML = html;
        });

 