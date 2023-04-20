# command to give executable permissions to this file : "chmod +x ./run.sh"

echo "Select RUN option: 1. mininet, 2. controller, 3. clear mn workflow"
read CHOICE_INPUT
case $CHOICE_INPUT in
1)
    # make sure controller is started
    echo "Running mininet topology"
    sudo python3 mininet/topology.py ;;
2)
    echo "Running RYU controller"
    # ryu-manager --verbose controller/l3_switch.py
    ryu-manager controller/l3_switch.py ;;
3)
    echo "Clear previous mininet workflow"
    sudo mn -c ;;
*)
    echo "Wrong option !!" ;;
esac