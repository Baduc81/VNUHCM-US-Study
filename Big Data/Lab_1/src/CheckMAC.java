import java.net.*;
import java.util.*;

public class CheckMAC {
    public static void main(String[] args) throws Exception {
        Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
        while (interfaces.hasMoreElements()) {
            NetworkInterface ni = interfaces.nextElement();
            System.out.println("Interface: " + ni.getName());

            try {
                byte[] mac = ni.getHardwareAddress();
                if (mac != null) {
                    System.out.print("  MAC: ");
                    for (int i = 0; i < mac.length; i++) {
                        System.out.format("%02X%s", mac[i], (i < mac.length - 1) ? "-" : "");
                    }
                    System.out.println();
                } else {
                    System.out.println("  MAC: null");
                }
            } catch (Exception e) {
                System.out.println("  Error reading MAC: " + e.getMessage());
            }
        }
    }
}
