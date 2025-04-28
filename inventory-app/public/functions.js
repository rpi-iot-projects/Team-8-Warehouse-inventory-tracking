function parseCSV(text) {
    const lines = text.trim().split('\n');
    return lines.map(line => line.split(','));
  }

  function createRow(itemCode = '', itemWeight = '1', itemPrice = '0000', totalWeight = '1') {
    const itemCount = itemWeight && totalWeight ? Math.ceil(totalWeight / itemWeight) : '';
    const timestamp = new Date().toISOString().replace(/[:T]/g, '-').split('.')[0];
    const tr = document.createElement('tr');

    tr.innerHTML = `
      <td id="long" contenteditable="true">${itemCode}</td>
      <td contenteditable="true">${itemWeight}</td>
      <td contenteditable="true">${itemPrice}</td>
      <td readonly>${totalWeight}</td>
      <td readonly>${itemCount}</td>
      <td readonly>${timestamp}</td>
      <td><button onclick="deleteRow(this)">Delete</button></td>
    `;
    return tr;
  }

  function handleCSVUpload(event) {
    const file = event.target.files[0];
    const reader = new FileReader();

    reader.onload = function(e) {
      const rows = parseCSV(e.target.result);
      const tableBody = document.querySelector('#inventoryTable tbody');
      tableBody.innerHTML = '';

      rows.forEach(row => {
        const [itemCode, itemWeight, itemPrice, totalWeight, temp, timestamp] = row;
        const itemCount = Math.ceil(totalWeight / itemWeight);
        const tr = document.createElement('tr');

        tr.innerHTML = `
          <td id="long" contenteditable="true">${itemCode}</td>
          <td contenteditable="true">${itemWeight}</td>
          <td contenteditable="true">${itemPrice}</td>
          <td readonly>${totalWeight}</td>
          <td readonly>${itemCount}</td>
          <td readonly>${timestamp}</td>
          <td><button onclick="deleteRow(this)">Delete</button></td>
        `;
        tableBody.appendChild(tr);
      });
    };

    reader.readAsText(file);
  }

  function downloadCSV() {
    const rows = [];
    document.querySelectorAll('#inventoryTable tbody tr').forEach(tr => {
      const cells = tr.querySelectorAll('td');
      const itemCode = cells[0].innerText;
      const itemWeight = parseFloat(cells[1].innerText);
      const itemPrice = cells[2].innerText;
      const totalWeight = parseFloat(cells[3].innerText);
      const itemCount = Math.ceil(totalWeight / itemWeight);
      const timestamp = cells[5].innerText;

      rows.push([itemCode, itemWeight, itemPrice, totalWeight, itemCount, timestamp]);
    });

    const csvContent = rows.map(e => e.join(",")).join("\n");
    //const timestamp = new Date().toISOString().replace(/[:T]/g, '-').split('.')[0];
    const filename = `inventory.csv`; //const filename = `inventory-${timestamp}.csv`;

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
  }

  function generateReport() {
    document.getElementById('dataSection').style.display = 'none';
    document.getElementById('reportImage').style.display = 'block';
    document.getElementById('backButton').style.display = 'inline';
  }

  function backToData() {
    document.getElementById('dataSection').style.display = 'block';
    document.getElementById('reportImage').style.display = 'none';
    document.getElementById('backButton').style.display = 'none';
  }

  function addRow() {
    const tr = createRow();
    document.querySelector('#inventoryTable tbody').appendChild(tr);
  }

  function deleteRow(button) {
    button.closest('tr').remove();
  }

  document.getElementById('csvFile').addEventListener('change', handleCSVUpload);