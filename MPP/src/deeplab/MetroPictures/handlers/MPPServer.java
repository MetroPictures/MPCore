package deeplab.MetroPictures.handlers;

import processing.net.*;

import org.json.*;

import deeplab.MetroPictures.MPPCore;

public class MPPServer {
	MPPCore parent;
	
	Server s;
	Client c;
	
	boolean is_running;
	
	public MPPServer(MPPCore parent) {
		this.parent = parent;
		is_running = false;
	}
	
	public void draw() {
		if(getStatus()) {
			try {
				c = s.available();
				
				if(c != null) {
					c.write(parent.onCommand(new JSONObject(c.readString().trim())).toString());
					return;
				}
			} catch(JSONException e) {
				System.out.println("NOT JSON!");
				System.out.println(c.readString().trim());
				
				JSONObject fail_response = new JSONObject();
				fail_response.put("response", false);
				fail_response.put("retry_command", true);
				
				c.write(fail_response.toString());
			} catch(NullPointerException e) {}
		}
	}
	
	public boolean start() {
		if(getStatus()) {
			return getStatus();
		}
		
		s = new Server(parent, 5050);
		return setStatus(true);
	}
	
	public boolean stop() {
		if(!getStatus()) {
			return !getStatus();
		}
		
		s.stop();
		return !setStatus(false);
	}
	
	private boolean setStatus(boolean new_status) {
		is_running = new_status;
		return getStatus();
	}
	
	public boolean getStatus() {
		return is_running;
	}
}
