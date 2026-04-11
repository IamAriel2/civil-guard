
window.addEventListener('DOMContentLoaded', function() {
    var planBtn = document.getElementById('plan-route-btn');
    var loader = document.getElementById('plan-route-loading');
    var btnText = document.getElementById('plan-route-btn-text');
    planBtn.disabled = true;
    loader.style.display = 'inline-block';
    btnText.style.opacity = 0.5;
});

Promise.all([
    new Promise(resolve => {
        if (document.readyState === 'complete') resolve();
        else window.addEventListener('load', resolve);
    }),
    fetch('shelters.json')
]).then(() => {
    var planBtn = document.getElementById('plan-route-btn');
    var loader = document.getElementById('plan-route-loading');
    var btnText = document.getElementById('plan-route-btn-text');
    if (planBtn && loader && btnText) {
        planBtn.disabled = false;
        loader.style.display = 'none';
        btnText.style.opacity = 1;
    }
});

// Center on Holon with higher zoom
var map = L.map('map').setView([32.0114, 34.7748], 15);

L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 20
}).addTo(map);

var redDotIcon = L.divIcon({
    className: 'red-dot',
    html: '<div style="background-color: #00FFF0; border-radius: 50%; width: 8px; height: 8px; box-shadow: 1px 1px 3px rgba(0,0,0,0.5);"></div>',
    iconSize: [8, 8],
    iconAnchor: [4, 4]
});

fetch('shelters.json')
    .then(response => response.json())
    .then(data => {
        data.forEach(shelter => {
            L.marker([shelter.coords[0], shelter.coords[1]], {icon: redDotIcon})
                .addTo(map)
                .bindPopup('<b>' + shelter.name + '</b><br>' + shelter.addr2 + '<br> 🛡️ מקלט ציבורי')
                .on('click', function(e) {
                    console.log('Clicked on shelter:', shelter.name, 'at', shelter.address);
                });
        });
    })
    .catch(error => console.error('Error loading shelters:', error));

const slider = document.getElementById('time-slider');
const sliderText = document.getElementById('slider-text');

slider.addEventListener('input', function() {
    sliderText.textContent = 'זמן הגעה למרחב המוגן: ' + slider.value + ' דק\' (' + (slider.value * 80) + ' מ' + "\')";
});

const safetySlider = document.getElementById('safety-slider');
const safetyText = document.getElementById('safety-text');

safetySlider.addEventListener('input', function() {
    safetyText.textContent = 'אחוז בטיחות: ' + safetySlider.value + '%';
});

document.getElementById('use_my_location').addEventListener('click', function() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            
            const originInput = document.getElementById('origin-input');
            originInput.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
            originInput.dispatchEvent(new Event('change'));
        }, function(error) {
            alert('לא הצלחנו לקבל את המיקום שלך. אנא בדוק הרשאות.');
        });
    } else {
        alert('הדפדפן שלך לא תומך במיקום.');
    }
});

const addressCache = {
    origin: { query: '', nodeId: null, coords: 'false' },
    destination: { query: '', nodeId: null, coords: 'false' }
};

async function fetchAddressNode(inputId, type) {
    const query = document.getElementById(inputId).value.trim();
    
    if (!query) return null;
    
    if (addressCache[type].query === query && addressCache[type].nodeId) {
        return addressCache[type].nodeId;
    }
    
    try {
        const res = await fetch(`/address?address=${encodeURIComponent(query)}`);
        const data = await res.json();
        
        addressCache[type].query = query;
        addressCache[type].nodeId = data.node_id || null;
        
        return addressCache[type].nodeId;
    } catch (error) {
        console.error(`Error fetching address for ${type}:`, error);
        return null;
    }
}

const timeSlider = document.getElementById('time-slider');
const RED_ZONE_PERCENT = 64.28;

function updateComplexSlider() {
    const value = parseInt(timeSlider.value);
    const min = parseInt(timeSlider.min);
    const max = parseInt(timeSlider.max);
    const currentPercent = ((value - min) / (max - min)) * 100;

    let gradient;

    if (currentPercent < RED_ZONE_PERCENT) {
        gradient = `linear-gradient(to left, 
            #007bff ${currentPercent}%
            #ccc ${RED_ZONE_PERCENT}%, 
            #ff4d4d 100%, )`
            ;
    } else {
        gradient = `linear-gradient(to left, 
            #007bff 0%, 
            #007bff ${currentPercent}%, 
            #ccc ${currentPercent}%, 
            #ccc 100%)`;
    }

    timeSlider.style.background = gradient;
}

timeSlider.addEventListener('input', updateComplexSlider);
updateComplexSlider();

updateSliderBackground(timeSlider);
updateSliderBackground(safetySlider);

document.getElementById('origin-input').addEventListener('change', () => fetchAddressNode('origin-input', 'origin'));
document.getElementById('destination-input').addEventListener('change', () => fetchAddressNode('destination-input', 'destination'));

document.getElementById('plan-route-btn').addEventListener('click', async function() {
    const startInput = document.getElementById('origin-input').value.trim();
    const destInput = document.getElementById('destination-input').value.trim();
    const m = document.getElementById('safety-slider').value / 100; // Assuming M is between 0 and 1
    const timeValue = document.getElementById('time-slider').value;
    const btn = document.getElementById('plan-route-btn');
    const loader = document.getElementById('plan-route-loading');
    const btnText = document.getElementById('plan-route-btn-text');

    if (!startInput || !destInput) {
        alert('אנא הזן מוצא ויעד.');
        return;
    }

    btn.disabled = true;
    loader.style.display = 'inline-block';
    btnText.textContent = '...מחשב מסלול';

    try {
        const startNode = await fetchAddressNode('origin-input', 'origin');

        if (!startNode) {
            alert('לא הצלחנו למצוא את המיקום של כתובת המוצא.');
            return;
        }

        const destNode = await fetchAddressNode('destination-input', 'destination');

        if (!destNode) {
            alert('לא הצלחנו למצוא את המיקום של כתובת היעד.');
            return;
        }

        const routeRes = await fetch(`/route?start=${encodeURIComponent(startNode)}&dest=${encodeURIComponent(destNode)}&M=${m}&time=${timeValue * 80}`);
        const data = await routeRes.json();
        
        console.log('Route planning result:', data);
        if (data.route && data.route.length > 0) {
            alert(`נמצא מסלול! מרחק: ${data.distance.toFixed(2)}`);
            
            if (window.currentRouteLayer) {
                map.removeLayer(window.currentRouteLayer);
            }
            window.currentRouteLayer = L.polyline(data.route, {color: 'turquoise', weight: 8, opacity: 0.7}).addTo(map);
            map.fitBounds(window.currentRouteLayer.getBounds());
            
        } else {
            alert('לא נמצא מסלול.');
        }
    } catch (error) {
        console.error('Error fetching route:', error);
        alert('שגיאה בתכנון המסלול.');
    } finally {
        btn.disabled = false;
        loader.style.display = 'none';
        btnText.textContent = 'תכנון דרך בטוחה';
    }
});