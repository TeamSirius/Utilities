
double standard_dev(ArrayList<double> L, double mean){
	int length = L.size();
	if (length <= 1){
		return 0;
	}
	double variance = 0;
	for( int i = 0; i < length; i++){
		variance += Math.pow( (L.get(i) - mean), 2);
	}
	variance /= (length - 1);
	return Math.sqrt(variance);
}

double mean_value(ArrayList<double> L){
	int length = L.size();
	if (length <= 0){
		return 0;
	}
	double sum = 0;
	for( int i = 0; i < length; i++){
		sum += L.get(i);
	}
	return sum / length;
}

import java.util.HashMap;

int SAMPLE_SIZE = 100;
HashMap<String, ArrayList<double>> MAC_Aggregator = new HashMap<String, ArrayList<double>>();
JSONObject temp;
String mac;

for(int i = 0; i < SAMPLE_SIZE; i++) {
    ListView items = (ListView) findViewById(R.id.list_of_access_points);
    Context context = getApplicationContext();
    AccessPointManager ap = new AccessPointManager(context);
    AccessPointListAdapter accessPointListAdapter = new AccessPointListAdapter(global_ctx, ap.getAccessPoints());
    items.setAdapter(accessPointListAdapter);

    for (AccessPoint point : ap.getAccessPoints()) {
        try {
        	temp = point.toJSON();
        	mac = temp.get("MAC");
        	if (! MAC_Aggregator.containsKey(mac) ){
        		MAC_Aggregator.put(mac, new ArrayList<double>());
        	}
        	MAC_Aggregator.get(mac).add( temp.get("strength") );
        } catch (JSONException e) {
            e.printStackTrace();
        }
    }
}

JSONArray all_objects = new JSONArray();
JSONObject send_data = new JSONObject();
Location selected_location = (Location) point_picker.getSelectedItem();
ArrayList<double> strengths;
float mean;
float std;
JSONObject representation;
for(String mac: MAC_Aggregator.keySet() ){
	strengths = MAC_Aggregator.get(mac);
	mean = mean_value(strengths);
	std = standard_dev(strengths,mean);
	representation = new JSONObject();
	representation.put("MAC", mac);
    representation.put("strength", mean);
    representation.put("std", std);
    all_objects.put(representation);
}
try {
	send_data.put("lid", selected_location.getId());
	send_data.put("APS", all_objects);
} catch (JSONException e) {
	e.printStackTrace();
}

PostAccessPointsTask post_access_points = new PostAccessPointsTask(getString(R.string.post_access_points), send_data, global_ctx);
post_access_points.execute();




