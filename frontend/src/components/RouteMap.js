import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icons for different stop types
const createCustomIcon = (color) => {
    return new L.Icon({
        iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });
};

const stopIcons = {
    'START': createCustomIcon('green'),
    'CURRENT': createCustomIcon('green'),
    'PICKUP': createCustomIcon('yellow'),
    'DROPOFF': createCustomIcon('red'),
    'FUEL': createCustomIcon('orange'),
    'REST': createCustomIcon('blue'),
    'OVERNIGHT': createCustomIcon('violet')
};

const RouteMap = ({ stops = [], routeCoordinates = [] }) => {
    const [validStops, setValidStops] = useState([]);
    const [stopPositions, setStopPositions] = useState([]);
    
    // Default center (US center) if no coordinates
    const defaultCenter = [39.8283, -98.5795];
    
    // Safely parse coordinate values
    const safeParseFloat = (value) => {
        if (value === undefined || value === null) return 0;
        const num = parseFloat(value);
        return isNaN(num) ? 0 : num;
    };

    // Calculate map center based on route
    const calculateCenter = () => {
        if (routeCoordinates && routeCoordinates.length > 0) {
            const validCoords = routeCoordinates.filter(coord => 
                coord && coord.length === 2 && 
                !isNaN(coord[0]) && !isNaN(coord[1])
            );
            
            if (validCoords.length === 0) return defaultCenter;
            
            const lats = validCoords.map(coord => coord[1]);
            const lngs = validCoords.map(coord => coord[0]);
            return [
                (Math.min(...lats) + Math.max(...lats)) / 2,
                (Math.min(...lngs) + Math.max(...lngs)) / 2
            ];
        }
        return defaultCenter;
    };

    // Convert coordinates for Leaflet [lat, lng] format with validation
    const convertCoordinates = (coords) => {
        if (!coords || coords.length === 0) return [];
        
        return coords
            .filter(coord => 
                coord && coord.length === 2 && 
                !isNaN(coord[0]) && !isNaN(coord[1])
            )
            .map(coord => {
                const lng = safeParseFloat(coord[0]);
                const lat = safeParseFloat(coord[1]);
                return [lat, lng]; // Convert [lng, lat] to [lat, lng]
            });
    };

    // Calculate distance between two coordinates in meters
    const calculateDistance = (coord1, coord2) => {
        if (!coord1 || !coord2 || coord1.length !== 2 || coord2.length !== 2) {
            return 0;
        }
        
        const lng1 = safeParseFloat(coord1[0]);
        const lat1 = safeParseFloat(coord1[1]);
        const lng2 = safeParseFloat(coord2[0]);
        const lat2 = safeParseFloat(coord2[1]);
        
        const R = 6371000; // Earth radius in meters
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLng = (lng2 - lng1) * Math.PI / 180;
        const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLng / 2) * Math.sin(dLng / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    };

    // Get total route distance in meters
    const getTotalRouteDistance = (coords) => {
        if (!coords || coords.length < 2) return 0;
        
        let totalDistance = 0;
        for (let i = 1; i < coords.length; i++) {
            totalDistance += calculateDistance(coords[i-1], coords[i]);
        }
        return totalDistance;
    };

    // Get stop positions based on distance percentage
    const calculateStopPositions = () => {
        if (!routeCoordinates || routeCoordinates.length === 0 || !validStops || validStops.length === 0) {
            return [];
        }
        
        const totalRouteDistance = getTotalRouteDistance(routeCoordinates);
        if (totalRouteDistance === 0) {
            // Distribute stops evenly along the route
            return validStops.map((stop, index) => {
                const positionIndex = Math.min(
                    Math.floor((index / validStops.length) * routeCoordinates.length),
                    routeCoordinates.length - 1
                );
                return routeCoordinates[positionIndex];
            });
        }
        
        return validStops.map(stop => {
            // Use cumulative distance in km, convert to meters for comparison
            const stopDistanceMeters = safeParseFloat(stop.cumulative_distance_km) * 1000;
            const stopPercentage = Math.min(stopDistanceMeters / totalRouteDistance, 1);
            
            // Find the segment where this stop belongs
            let accumulatedDistance = 0;
            for (let i = 1; i < routeCoordinates.length; i++) {
                const segmentDistance = calculateDistance(routeCoordinates[i-1], routeCoordinates[i]);
                
                if (accumulatedDistance + segmentDistance >= stopDistanceMeters) {
                    // Interpolate position within this segment
                    const fraction = (stopDistanceMeters - accumulatedDistance) / segmentDistance;
                    const lng = routeCoordinates[i-1][0] + (routeCoordinates[i][0] - routeCoordinates[i-1][0]) * fraction;
                    const lat = routeCoordinates[i-1][1] + (routeCoordinates[i][1] - routeCoordinates[i-1][1]) * fraction;
                    return [lng, lat];
                }
                accumulatedDistance += segmentDistance;
            }
            
            // Fallback to end of route
            return routeCoordinates[routeCoordinates.length - 1] || [-98.5795, 39.8283];
        });
    };

    // Filter and validate stops
    useEffect(() => {
        if (!stops || !Array.isArray(stops)) {
            setValidStops([]);
            return;
        }
        
        const filteredStops = stops.filter(stop => 
            stop && 
            stop.type && 
            stop.location &&
            stop.cumulative_distance_km !== undefined &&
            stop.cumulative_distance_km !== null
        ).map(stop => ({
            ...stop,
            cumulative_distance_km: safeParseFloat(stop.cumulative_distance_km),
            cumulative_distance_miles: safeParseFloat(stop.cumulative_distance_miles),
            stop_duration: safeParseFloat(stop.stop_duration)
        }));
        
        setValidStops(filteredStops);
    }, [stops]);

    // Calculate stop positions when stops or route changes
    useEffect(() => {
        if (validStops.length > 0 && routeCoordinates.length > 0) {
            const positions = calculateStopPositions();
            // Filter out any invalid positions
            const validPositions = positions.filter(pos => 
                pos && pos.length === 2 && 
                !isNaN(pos[0]) && !isNaN(pos[1])
            );
            setStopPositions(validPositions);
        } else {
            setStopPositions([]);
        }
    }, [validStops, routeCoordinates]);

    const mapCenter = calculateCenter();
    const polylinePositions = convertCoordinates(routeCoordinates);

    // Get icon for stop type with fallback
    const getStopIcon = (stopType) => {
        return stopIcons[stopType] || stopIcons.PICKUP;
    };

    return (
        <div style={{ position: 'relative', width: '100%', height: '400px' }}>
            <MapContainer
                center={mapCenter}
                zoom={5}
                style={{ height: '100%', width: '100%', borderRadius: '8px' }}
                scrollWheelZoom={true}
                key={`map-${polylinePositions.length}-${validStops.length}`} // Force re-render when data changes
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {/* Route Polyline */}
                {polylinePositions.length > 1 && (
                    <Polyline
                        positions={polylinePositions}
                        color="blue"
                        weight={4}
                        opacity={0.7}
                    />
                )}

                {/* Stop Markers */}
                {validStops.map((stop, index) => {
                    if (index >= stopPositions.length) return null;
                    
                    const position = stopPositions[index];
                    if (!position || position.length !== 2 || isNaN(position[0]) || isNaN(position[1])) {
                        return null;
                    }
                    
                    // Convert to [lat, lng] for Leaflet
                    const leafletPosition = [position[1], position[0]];
                    
                    return (
                        <Marker
                            key={`${stop.type}-${index}-${position[0]}-${position[1]}`}
                            position={leafletPosition}
                            icon={getStopIcon(stop.type)}
                        >
                            <Popup>
                                <div>
                                    <strong>{stop.type}</strong>
                                    <br />
                                    <strong>Location:</strong> {stop.location}
                                    <br />
                                    <strong>Distance:</strong> {safeParseFloat(stop.cumulative_distance_km).toFixed(1)} km ({safeParseFloat(stop.cumulative_distance_miles).toFixed(1)} miles)
                                    <br />
                                    <strong>Stop Duration:</strong> {safeParseFloat(stop.stop_duration).toFixed(1)} hours
                                    <br />
                                    <strong>Day:</strong> {stop.day || 1}
                                    {stop.notes && (
                                        <>
                                            <br />
                                            <strong>Notes:</strong> {stop.notes}
                                        </>
                                    )}
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>
            
            {/* Loading/Error overlay */}
            {polylinePositions.length === 0 && (
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: 'rgba(255, 255, 255, 0.8)',
                    zIndex: 1000,
                    borderRadius: '8px'
                }}>
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                        <h3>Loading Route Map...</h3>
                        <p>If this takes too long, the routing service might be temporarily unavailable.</p>
                        <p>Try refreshing or check your coordinates.</p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default RouteMap;