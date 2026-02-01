package com.preponderous.roam.dto;

/**
 * DTO for entity information.
 * 
 * TODO: Consider adding Lombok to reduce boilerplate getters/setters across all DTOs
 *       This would reduce code duplication and improve maintainability.
 *       Example: @Data, @NoArgsConstructor, @AllArgsConstructor annotations
 * 
 * @author Daniel McCoy Stephenson
 */
public class EntityDTO {
    private String id;
    private String name;
    private String type;
    private String imagePath;
    private String locationId;
    private boolean solid;
    
    // LivingEntity fields (optional, null if not a living entity)
    private Double energy;
    private Double targetEnergy;
    
    // Harvestable fields (Tree, Rock, Bush)
    private Integer harvestCount;
    private Integer maxHarvestCount;
    private Boolean canHarvest;
    
    // Resource fields (Apple, Berry)
    private Double energyValue;
    
    // Resource quantity fields (Wood, Stone)
    private Integer quantity;
    
    // Wildlife fields
    private Integer moveSpeed;
    private Double aggressionRange;
    private Double fleeRange;
    private Boolean aggressive;

    public EntityDTO() {
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getImagePath() {
        return imagePath;
    }

    public void setImagePath(String imagePath) {
        this.imagePath = imagePath;
    }

    public String getLocationId() {
        return locationId;
    }

    public void setLocationId(String locationId) {
        this.locationId = locationId;
    }

    public boolean isSolid() {
        return solid;
    }

    public void setSolid(boolean solid) {
        this.solid = solid;
    }

    public Double getEnergy() {
        return energy;
    }

    public void setEnergy(Double energy) {
        this.energy = energy;
    }

    public Double getTargetEnergy() {
        return targetEnergy;
    }

    public void setTargetEnergy(Double targetEnergy) {
        this.targetEnergy = targetEnergy;
    }

    public Integer getHarvestCount() {
        return harvestCount;
    }

    public void setHarvestCount(Integer harvestCount) {
        this.harvestCount = harvestCount;
    }

    public Integer getMaxHarvestCount() {
        return maxHarvestCount;
    }

    public void setMaxHarvestCount(Integer maxHarvestCount) {
        this.maxHarvestCount = maxHarvestCount;
    }

    public Boolean getCanHarvest() {
        return canHarvest;
    }

    public void setCanHarvest(Boolean canHarvest) {
        this.canHarvest = canHarvest;
    }

    public Double getEnergyValue() {
        return energyValue;
    }

    public void setEnergyValue(Double energyValue) {
        this.energyValue = energyValue;
    }

    public Integer getQuantity() {
        return quantity;
    }

    public void setQuantity(Integer quantity) {
        this.quantity = quantity;
    }

    public Integer getMoveSpeed() {
        return moveSpeed;
    }

    public void setMoveSpeed(Integer moveSpeed) {
        this.moveSpeed = moveSpeed;
    }

    public Double getAggressionRange() {
        return aggressionRange;
    }

    public void setAggressionRange(Double aggressionRange) {
        this.aggressionRange = aggressionRange;
    }

    public Double getFleeRange() {
        return fleeRange;
    }

    public void setFleeRange(Double fleeRange) {
        this.fleeRange = fleeRange;
    }

    public Boolean getAggressive() {
        return aggressive;
    }

    public void setAggressive(Boolean aggressive) {
        this.aggressive = aggressive;
    }
}
