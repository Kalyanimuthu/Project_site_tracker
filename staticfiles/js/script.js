function openEntryModal(event) {
    event.preventDefault();

    let siteId = document.getElementById("siteId").value;
    let from_date = document.getElementById("from_date").value;
    let to_date = document.getElementById("to_date").value;

    fetch(`/${siteId}/filter-entries/?from_date=${from_date}&to_date=${to_date}`)
        .then(async (res) => {
            if (!res.ok) {
                let text = await res.text();
                throw new Error(text);
            }
            return res.json();
        })
        .then(data => {
            if (data.error) {
                alert("Server Error: " + data.error);
                return;
            }

            document.getElementById("modalBody").innerHTML = data.html;

            let modal = new bootstrap.Modal(document.getElementById("entryModal"));
            modal.show();
        })
        .catch(err => {
            console.error("Error loading modal:", err);
            alert("Unable to load entry details.\n\n" + err);
        });
}


function filterBySection(section) {
    const siteId = document.getElementById("siteId").value;

    fetch(`/${siteId}/filter-section/?section=${section}`)
        .then(res => res.json())
        .then(data => {
            document.getElementById("modalBody").innerHTML = data.html;
            new bootstrap.Modal(document.getElementById("entryModal")).show();
        })
        .catch(err => alert("Error loading filter: " + err));
}
